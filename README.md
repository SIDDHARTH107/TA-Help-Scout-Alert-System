# 🚨 TA Help Scout Alert System

An automated SLA monitoring and alert pipeline that tracks student support ticket response times in Help Scout and sends real-time Slack alerts when tickets breach configurable SLA thresholds. Built to ensure no student support ticket goes unanswered.

---

## 📌 Problem

As a Teaching Assistant at Northeastern University, our TA team manages **70+ student support tickets** across **5+ courses** using Help Scout. The challenge:

- Tickets would sit unanswered for **10–18 hours** because no one was actively tracking them
- TAs only saw tickets when they **manually opened Help Scout**
- During busy weeks (project deadlines), tickets **mostly goes unanswered because of unavailability of TAs**
- There was **no system** to flag overdue tickets or alert the team

## 💡 Solution

A lightweight Python automation that runs every 3 hours via GitHub Actions, checks all open Help Scout tickets, and sends a Slack alert to the TA team whenever tickets exceed the SLA threshold — **without any manual effort**.

### Sample Screenshots

<img width="1529" height="698" alt="image" src="https://github.com/user-attachments/assets/b1262ace-909b-4cdb-a104-42072dcaaee6" />

<img width="1875" height="859" alt="image" src="https://github.com/user-attachments/assets/d7dea226-93cb-4e7b-8228-fae8b0c884a2" />

<img width="1915" height="964" alt="image" src="https://github.com/user-attachments/assets/243829b1-a3da-413f-afce-ddc8d7001524" />

### Sample Slack Alert

```
🚨 SLA Alert: 3 ticket(s) need attention!
Threshold: 1.0 hour(s)
───────────────────────────

🔴 A New Extension Request Submitted!
    👤 Student: Katie Freedman
    📚 Course: INFO5100
    ⏱️ Waiting: 21.1 hours

🟠 IE 7300 Homework 8
    👤 Student: Kat Fountain
    📚 Course: IE7300
    ⏱️ Waiting: 18.6 hours

🟡 Re: MGMT6214
    👤 Student: Lauren Johnson
    📚 Course: No course tag
    ⏱️ Waiting: 6.4 hours

───────────────────────────
💡 Please check Help Scout and respond to these tickets.
🕐 Alert generated at: 2026-04-13 21:44 UTC
```

## 🏗️ Architecture

```
GitHub Actions (scheduled cron job - every 3 hours)
    │
    ▼
Python Script (sla_monitor.py)
    │
    ├──► Authenticate with Help Scout (OAuth2 Client Credentials)
    │
    ├──► Fetch all open/active conversations (Help Scout REST API v2)
    │
    ├──► Calculate wait time for each ticket
    │        • 🟡 Approaching  (1x threshold)
    │        • 🟠 Warning      (2x threshold)
    │        • 🔴 Critical     (3x threshold)
    │
    ├──► Send formatted alert to Slack (Incoming Webhook)
    │
    └──► Save alert log (JSON) for historical tracking
```

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.12 | Core script |
| API | Help Scout REST API v2 | Fetch open ticket data |
| Authentication | OAuth2 (Client Credentials) | Secure API access |
| Notifications | Slack Incoming Webhooks | Real-time team alerts |
| Automation | GitHub Actions (Cron) | Scheduled execution every 3 hours |
| Config | python-dotenv | Environment variable management |
| Logging | JSON file | Alert history tracking |

## 📁 Project Structure

```
TA-Help-Scout-Alert-System/
├── .github/
│   └── workflows/
│       └── sla_check.yml       # GitHub Actions workflow (runs every 3 hrs)
├── logs/
│   └── alert_history.json      # Alert history log
├── .env                        # API keys & secrets (not tracked in git)
├── .gitignore                  # Excludes .env, venv, logs
├── requirements.txt            # Python dependencies
├── sla_monitor.py              # Main monitoring script
└── README.md
```

## 🚀 Setup & Installation

### Prerequisites

- Python 3.10+
- Help Scout account with API access
- Slack workspace with a dedicated alerts channel

### 1. Clone the Repository

```bash
git clone https://github.com/SIDDHARTH107/TA-Help-Scout-Alert-System.git
cd TA-Help-Scout-Alert-System
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
HELPSCOUT_APP_ID=your_app_id_here
HELPSCOUT_APP_SECRET=your_app_secret_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
SLA_THRESHOLD_HOURS=1
```

**Help Scout credentials:** Profile → My Apps → Create My App

**Slack webhook:** [Slack API](https://api.slack.com/apps) → Create App → Incoming Webhooks → Add to Workspace

### 5. Run Locally

```bash
python sla_monitor.py
```

### 6. Deploy with GitHub Actions

Add the following as **Repository Secrets** in GitHub (Settings → Secrets → Actions):

- `HELPSCOUT_APP_ID`
- `HELPSCOUT_APP_SECRET`
- `SLACK_WEBHOOK_URL`
- `SLA_THRESHOLD_HOURS`

The workflow runs automatically every 3 hours. To trigger manually: **Actions → TA Help Scout Alert System → Run workflow**.

## ⚙️ Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SLA_THRESHOLD_HOURS` | Hours before a ticket triggers an alert | `1` |
| Cron Schedule | How often the check runs (in `sla_check.yml`) | Every 3 hours |

### Severity Levels

| Icon | Level | Condition |
|------|-------|-----------|
| 🟡 | Approaching | Wait time ≥ 1x threshold |
| 🟠 | Warning | Wait time ≥ 2x threshold |
| 🔴 | Critical | Wait time ≥ 3x threshold |

## 📊 Alert Details

Each alert includes:

- **Ticket subject** — the student's email subject line
- **Student name** — extracted from Help Scout's primary customer field
- **Course tag** — auto-detected from Help Scout tags (e.g., INFO5100, DADS7275, SCHM6318)
- **Wait time** — hours since ticket was created
- **Severity indicator** — color-coded based on how far past the SLA threshold

## 👤 Author

**Siddharth Mohapatra**
- Teaching Assistant, Innovation Lab - JM @Northeastern University EDGE department
- Master's in Data Analytics Engineering, Northeastern University
- [GitHub](https://github.com/SIDDHARTH107)
- [LinkedIn](https://www.linkedin.com/in/siddharthmohapatra-dataanalyst/)
