import os
import json
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Loading enviroment variables
load_dotenv()

HELPSCOUT_APP_ID = os.getenv("HELPSCOUT_APP_ID")
HELPSCOUT_APP_SECRET = os.getenv("HELPSCOUT_APP_SECRET")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLA_THRESHOLD_HOURS = float(os.getenv("SLA_THRESHOLD_HOURS", 1))

HELPSCOUT_BASE_URL = "https://api.helpscout.net/v2"

# Step1: Authentication with Help Scout
def get_access_token():
    """Get OAuth2 access token from Help Scout."""
    response = requests.post(
        f"{HELPSCOUT_BASE_URL}/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": HELPSCOUT_APP_ID,
            "client_secret": HELPSCOUT_APP_SECRET
        }
    )
    
    # Debug: See the actual error message
    # print(f"Status Code: {response.status_code}")
    # print(f"Response Body: {response.text}")
    
    response.raise_for_status()
    token = response.json()["access_token"]
    print("✅ Authenticated with Help Scout")
    return token

# Step 2: Fetching all open/active conversations
def get_open_conversations(token):
    """Pull all active (open) conversations from Help Scout."""
    headers = {"Authorization": f"Bearer {token}"}
    conversations = []
    page = 1

    while True:
        response = requests.get(
            f"{HELPSCOUT_BASE_URL}/conversations",
            headers=headers,
            params={
                "status": "active",
                "page": page,
                "sortField": "createdAt",
                "sortOrder": "asc"
            }
        )
        response.raise_for_status()
        data = response.json()

        if "_embedded" not in data:
            break

        conversations.extend(data["_embedded"]["conversations"])

        total_pages = data["page"]["totalPages"]
        if page >= total_pages:
            break

        page += 1

    print(f"📬 Found {len(conversations)} open conversations")
    return conversations

# Step 3: Checking which tickets have exceeded the SLA (Service Level Agreement)
def check_sla_breaches(conversations):
    """Find conversations waiting longer than the SLA threshold."""
    breached_tickets = []
    now = datetime.now(timezone.utc)

    for conv in conversations:
        # Parsing the creation time
        created_at = datetime.fromisoformat(conv["createdAt"].replace("Z", "+00:00"))
        wait_hours = (now - created_at).total_seconds() / 3600

        if wait_hours >= SLA_THRESHOLD_HOURS:
            # Extracting student name
            if "primaryCustomer" in conv:
                student_name = (
                    conv["primaryCustomer"].get("first", "") + " " +
                    conv["primaryCustomer"].get("last", "")
                ).strip()
            else:
                student_name = "Unknown"

            # Extracting course tag
            tags = [tag["tag"] for tag in conv.get("tags", [])]
            course_tag = "No course tag"
            for tag in tags:
                # Matching patterns like dads7275, info5100, schm6318, etc.
                tag_lower = tag.lower()
                if any(prefix in tag_lower for prefix in ["dads", "info", "schm", "strt", "ie"]):
                    course_tag = tag.upper()
                    break

            # Determining the severity based on wait time
            if wait_hours >= SLA_THRESHOLD_HOURS * 3:
                severity = "🔴"  # Critical
            elif wait_hours >= SLA_THRESHOLD_HOURS * 2:
                severity = "🟠"  # Warning
            else:
                severity = "🟡"  # Approaching

            breached_tickets.append({
                "subject": conv.get("subject", "No subject"),
                "student_name": student_name,
                "course_tag": course_tag,
                "wait_hours": round(wait_hours, 1),
                "severity": severity,
                "conversation_id": conv["id"],
                "all_tags": tags
            })

    # Sorting by wait time (longest first)
    breached_tickets.sort(key=lambda x: x["wait_hours"], reverse=True)

    print(f"⚠️ {len(breached_tickets)} tickets have breached the {SLA_THRESHOLD_HOURS}hr SLA")
    return breached_tickets

# Step 4: Sending the Slack alerts
def send_slack_alert(breached_tickets):
    """Sending a formatted alert to the Slack channel."""
    if not breached_tickets:
        print("✅ No SLA breaches. No alert sent.")
        return

    # Building the Slack message
    header = (
        f"🚨 *SLA Alert: {len(breached_tickets)} ticket(s) need attention!*\n"
        f"Threshold: {SLA_THRESHOLD_HOURS} hour(s)\n"
        f"───────────────────────────"
    )

    ticket_lines = []
    for ticket in breached_tickets:
        line = (
            f"\n{ticket['severity']} *{ticket['subject']}*\n"
            f"    👤 Student: {ticket['student_name']}\n"
            f"    📚 Course: {ticket['course_tag']}\n"
            f"    ⏱️ Waiting: *{ticket['wait_hours']} hours*\n"
        )
        ticket_lines.append(line)

    footer = (
        f"\n───────────────────────────\n"
        f"💡 _Please check Help Scout and respond to these tickets._\n"
        f"🕐 Alert generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
    )

    message = header + "".join(ticket_lines) + footer

    # Sending to Slack
    response = requests.post(
        SLACK_WEBHOOK_URL,
        json={"text": message}
    )

    if response.status_code == 200:
        print(f"✅ Slack alert sent for {len(breached_tickets)} tickets")
    else:
        print(f"❌ Slack alert failed: {response.status_code} - {response.text}")

# Step 5: Saving a log for tracking history
def save_log(breached_tickets):
    """Saving alert history to a log file."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sla_threshold_hours": SLA_THRESHOLD_HOURS,
        "total_breaches": len(breached_tickets),
        "tickets": breached_tickets
    }

    log_file = "logs/alert_history.json"

    # Loading existing logs or creating new
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(log_entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)

    print(f"📝 Log saved to {log_file}")

# Main: Running everything
def main():
    print("=" * 50)
    print("🔍 HelpWatch SLA Monitor - Starting check...")
    print(f"⏰ SLA Threshold: {SLA_THRESHOLD_HOURS} hour(s)")
    print("=" * 50)

    # Step 1: Authenticate
    token = get_access_token()

    # Step 2: Get open conversations
    conversations = get_open_conversations(token)

    # Step 3: Check for SLA breaches
    breached_tickets = check_sla_breaches(conversations)

    # Step 4: Send Slack alert (only if there are breaches)
    send_slack_alert(breached_tickets)

    # Step 5: Save log
    save_log(breached_tickets)

    print("\n✅ SLA check complete!")

if __name__ == "__main__":
    main()