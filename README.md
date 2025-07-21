# RSS Security Alert Filter with JIRA Integration

This script monitors multiple RSS feeds for security alerts related to specific products and threats, then creates JIRA tickets with Slack notifications and automated acknowledgment workflows.

## Features

- **Multi-Source RSS Filtering**: Monitors BleepingComputer, CISA, HackerNews, Krebs, and DarkReading RSS feeds
- **Keyword Matching**: Filters entries based on customizable product and threat keywords
- **Slack Integration**: Posts formatted alerts to Slack with source, title, and JIRA ticket links
- **JIRA Integration**: Creates JIRA tickets as subtasks linked to a security epic
- **Automated Acknowledgment**: Monitors for thumbs up reactions and assigns tickets to the first person who acknowledges
- **Ticket Status Management**: Automatically transitions tickets to "In Progress" upon acknowledgment
- **Duplicate Prevention**: Uses cache files to avoid creating duplicate tickets
- **Acknowledgment Monitoring**: Separate script to continuously check for acknowledgments and manage ticket assignments

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Set the following environment variables:

```bash
# Slack Configuration
export SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"
export SLACK_CHANNEL_ID="C1234567890"

# JIRA Configuration
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your-jira-api-token"
export JIRA_EPIC_KEY="SEC-123"  # The epic key where tickets will be created as subtasks
export JIRA_PROJECT_KEY="SEC"   # The project key for ticket creation
```

### 3. Slack Bot Setup

The Slack bot requires the following scopes:
- `chat:write` - To post messages
- `reactions:read` - To monitor for thumbs up reactions
- `users:read` - To get user information
- `users:read.email` - To get user email for JIRA assignment

### 4. JIRA API Token Setup

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "RSS Alert Bot")
4. Copy the token and use it as `JIRA_API_TOKEN`

### 5. Epic Setup

Create a JIRA epic in your security project (e.g., "SEC-123") that will serve as the parent for all security alert tickets.

## Usage

Run any of the filter scripts:

```bash
python filter_rss_bleeping.py
python filter_rss_cisa.py
python filter_rss_hackernews.py
python filter_rss_krebs.py
python filter_rss_darkreading.py
```

## How It Works

### 1. RSS Processing
1. **RSS Parsing**: Fetches and parses the RSS feed
2. **Keyword Filtering**: Matches entries against customizable product and threat keyword lists
3. **Duplicate Check**: Uses a cache file to track previously processed entries

### 2. Alert Creation
4. **JIRA Ticket Creation**: For each new alert:
   - Creates a subtask under the specified epic
   - Sets medium priority
   - Includes comprehensive description with source link and detected keywords
   - Adds relevant labels
5. **Slack Notification**: Posts formatted alerts to the configured Slack channel

### 3. Acknowledgment Workflow
6. **Reaction Monitoring**: Continuously monitors for thumbs up reactions on the Slack message
7. **User Assignment**: First person to react gets assigned the JIRA ticket (using their Slack email)
8. **Status Update**: Ticket automatically transitions to "In Progress"
9. **Confirmation**: Bot posts acknowledgment message in the Slack thread
10. **Cache Update**: Updates the cache file with new entry links

## Slack Message Format

Alerts are posted in a clean, consistent format with unique emojis for each source:

```
🧠 Source: BleepingComputer
Title: [Article Title]
JIRA Ticket: SEC-123
```

**Source Emojis:**
- **🧠 BleepingComputer** - Brain emoji for intelligence/security news
- **🛡️ CISA** - Shield emoji for government security advisories
- **📰 HackerNews** - Newspaper emoji for tech news
- **🔍 Krebs** - Magnifying glass emoji for investigative journalism
- **🌙 DarkReading** - Moon emoji for "dark" security news

The ticket number is a clickable link that takes you directly to the JIRA ticket.

## Acknowledgment Workflow

1. **Alert Posted**: Security alert appears in Slack with JIRA ticket link
2. **User Acknowledges**: Team member reacts with thumbs up (👍)
3. **Automatic Assignment**: First person to react gets assigned the JIRA ticket
4. **Status Update**: Ticket automatically transitions to "In Progress"
5. **Confirmation**: Bot posts acknowledgment message in the thread

**Note**: Only the first thumbs up reaction triggers the assignment and status change to prevent multiple assignments.

## JIRA Ticket Structure

Each ticket includes:
- **Title**: The RSS entry title (truncated if too long)
- **Description**: 
  - Source information and publication date
  - Original RSS description
  - Detected product and threat keywords
  - Action required section
  - Auto-generation timestamp
- **Type**: Sub-task (linked to the security epic)
- **Priority**: Medium
- **Labels**: security-alert, rss-feed, [source], auto-generated, cti

## Customization

### Keywords

You can customize the keyword lists in each script:

- `PRODUCT_KEYWORDS`: Add products and technologies your organization uses
- `THREAT_KEYWORDS`: Add security threat terms that will trigger alerts
- `OTHER_KEYWORDS`: Add company names, industry-specific terms, or other relevant keywords

### JIRA Fields

You can customize the JIRA ticket creation by modifying the `issue_data` dictionary in the `create_jira_ticket()` function.

## Troubleshooting

### Common Issues

1. **JIRA Authentication Error**: Verify your email and API token
2. **Epic Not Found**: Ensure the epic key exists and is accessible
3. **Permission Issues**: Verify the JIRA user has permission to create issues in the project
4. **Slack Bot Permissions**: Ensure the bot has the required scopes, especially `users:read.email`
5. **Rate Limiting**: JIRA has API rate limits; the script includes error handling

### Debug Mode

The script includes detailed logging. Check the console output for:
- ✅ Success messages for created tickets
- ❌ Error messages for failed operations
- 📋 Summary of created tickets
- 👍 Thumbs up detection and assignment messages

## Files

### Main Scripts
- `filter_rss_bleeping.py`: BleepingComputer RSS filter
- `filter_rss_cisa.py`: CISA advisories RSS filter
- `filter_rss_hackernews.py`: HackerNews RSS filter
- `filter_rss_krebs.py`: Krebs on Security RSS filter
- `filter_rss_darkreading.py`: DarkReading RSS filter
- `check_acknowledgments.py`: Monitors Slack for acknowledgments and manages JIRA ticket assignments

### Support Files
- `requirements.txt`: Python dependencies
- `.seen_entries_*.json`: Cache files (auto-generated)
- `.message_ticket_mappings.json`: Acknowledgment tracking file (auto-generated)
- `feeds/*.xml`: Filtered RSS feed outputs

## Required Environment Variables

The RSS filter system requires these environment variables:

- `JIRA_URL` - Your JIRA instance URL
- `JIRA_EMAIL` - JIRA user email
- `JIRA_API_TOKEN` - JIRA API token
- `JIRA_EPIC_KEY` - Parent epic key for tickets
- `JIRA_PROJECT_KEY` - JIRA project key
- `SLACK_BOT_TOKEN` - Slack bot token with `users:read.email` scope
- `SLACK_CHANNEL_ID` - Target Slack channel ID

## GitHub Actions Workflows

Each RSS source has its own GitHub Actions workflow that can be triggered manually:

- **🔄 BleepingComputer RSS Filter** - `.github/workflows/rss-filter-bleeping.yml`
- **🔄 CISA RSS Filter** - `.github/workflows/rss-filter-cisa.yml`
- **🔄 HackerNews RSS Filter** - `.github/workflows/rss-filter-hackernews.yml`
- **🔄 Krebs RSS Filter** - `.github/workflows/rss-filter-krebs.yml`
- **🔄 DarkReading RSS Filter** - `.github/workflows/rss-filter-darkreading.yml`

### Setting up GitHub Actions

1. **Add Secrets**: Go to your repository Settings → Secrets and variables → Actions
2. **Add Required Secrets**:
   - `SLACK_BOT_TOKEN`
   - `SLACK_CHANNEL_ID`
   - `JIRA_URL`
   - `JIRA_EMAIL`
   - `JIRA_API_TOKEN`
   - `JIRA_EPIC_KEY`
   - `JIRA_PROJECT_KEY`
3. **Run Workflows**: Go to the Actions tab and manually trigger any workflow

### Workflow Features

- **Manual Trigger**: All workflows use `workflow_dispatch` for manual execution
- **Cache Management**: Automatically caches seen entries to prevent duplicates
- **Environment Variables**: Uses GitHub Secrets for secure credential management
- **Error Handling**: Continues execution even if cache save fails

## Acknowledgment Monitoring System

The `check_acknowledgments.py` script provides continuous monitoring of Slack messages for acknowledgment reactions and automated JIRA ticket management.

### Features

- **Message Monitoring**: Checks the last 100 messages in the configured Slack channel
- **Pattern Recognition**: Identifies JIRA ticket references using multiple patterns:
  - Standard bot format: `JIRA Ticket: <***/browse/SPCOPS-1975|SPCOPS-1975>`
  - Plain text references: `SPCOPS-1975`
  - JIRA URLs: `https://.../browse/SPCOPS-1975`
- **Reaction Detection**: Monitors for thumbs up reactions (👍, +1, thumbs_up)
- **User Assignment**: Automatically assigns JIRA tickets to the first person who acknowledges
- **Status Management**: Transitions tickets to "In Progress" upon acknowledgment
- **Thread Management**: Posts acknowledgment confirmations in Slack threads
- **Duplicate Prevention**: Checks thread replies to avoid duplicate processing
- **File Management**: Automatically cleans up old mappings (older than 24 hours)

### Usage

```bash
python check_acknowledgments.py
```

### How It Works

1. **Message Retrieval**: Fetches recent messages from the configured Slack channel
2. **Ticket Detection**: Identifies messages containing JIRA ticket references
3. **Acknowledgment Check**: Looks for thumbs up reactions on ticket messages
4. **User Processing**: Gets user information and email for JIRA assignment
5. **Ticket Management**: 
   - Assigns the ticket to the acknowledging user
   - Sets the "Triage Started" timestamp field
   - Transitions the ticket to "In Progress" status
6. **Confirmation**: Posts acknowledgment message in the Slack thread
7. **Tracking**: Maintains a mapping file to prevent duplicate processing

### Example Workflow

The acknowledgment system handles two different scenarios:

#### Scenario 1: Immediate Acknowledgment (During RSS Script)
When someone acknowledges the alert while the RSS script is still running (within the 1-minute timeout):

![Immediate Acknowledgment](images/immediate-acknowledgment.png)

**Workflow Steps:**
1. **Initial Alert**: Security Team Bot posts a DarkReading security alert with JIRA ticket link
2. **Quick Acknowledgment**: Team member (Taiga Walker) reacts with thumbs up 👍 within 1 minute
3. **Immediate Processing**: The RSS script's `monitor_for_thumbs_up` function detects the reaction
4. **Confirmation**: Bot posts acknowledgment confirmation with user mention and checkmark ✅

#### Scenario 2: Delayed Acknowledgment (After RSS Script)
When acknowledgment occurs after the RSS script has completed (handled by `check_acknowledgments.py`):

![Delayed Acknowledgment](images/acknowledgment-workflow.png)

**Workflow Steps:**
1. **Initial Alert**: Security Team Bot posts a Krebs security alert with JIRA ticket link
2. **Ticket Creation**: Bot creates JIRA ticket and posts confirmation in thread
3. **Delayed Acknowledgment**: Team member reacts with thumbs up 👍 after RSS script timeout
4. **Background Processing**: `check_acknowledgments.py` detects the reaction during its next run
5. **Confirmation**: Bot posts acknowledgment confirmation with user mention and checkmark ✅

Both scenarios result in the same outcome: automatic ticket assignment, status transition to "In Progress", and acknowledgment confirmation in the Slack thread.

> **Note**: To add the actual screenshots, save your Slack thread screenshots as:
> - `images/immediate-acknowledgment.png` (for quick acknowledgments)
> - `images/acknowledgment-workflow.png` (for delayed acknowledgments)
> 
> See `images/README.md` for detailed instructions.

### Statistics and Reporting

The script provides detailed statistics including:
- Number of JIRA ticket messages found
- Messages skipped (already processed)
- Messages checked for new acknowledgments
- New acknowledgments processed

### File Management

- **`.message_ticket_mappings.json`**: Tracks processed messages and acknowledgments
- **Automatic Cleanup**: Removes mappings older than 24 hours to prevent file bloat
- **Error Handling**: Graceful handling of API failures and missing data

### Required Environment Variables

The acknowledgment monitoring system requires these environment variables:

- `JIRA_URL` - Your JIRA instance URL
- `JIRA_EMAIL` - JIRA user email
- `JIRA_API_TOKEN` - JIRA API token
- `SLACK_BOT_TOKEN` - Slack bot token with required scopes
- `SLACK_CHANNEL_ID` - Target Slack channel ID

### Slack Bot Scopes Required

- `chat:write` - To post acknowledgment messages
- `reactions:read` - To monitor for thumbs up reactions
- `users:read` - To get user information
- `users:read.email` - To get user email for JIRA assignment
- `channels:history` - To read channel messages
- `groups:history` - To read private channel messages (if applicable)

---

## 📦 Current Feed Sources

| Feed Source         | Script Path                            | Output XML                          |
|---------------------|----------------------------------------|-------------------------------------|
| Hacker News         | `filter_rss_hackernews.py`             | `feeds/hackernews-products.xml`     |
| CISA Advisories     | `filter_rss_cisa.py`                   | `feeds/cisa-products.xml`           |
| BleepingComputer    | `filter_rss_bleeping.py`               | `feeds/bleeping-products.xml`       |
| Krebs on Security   | `filter_rss_krebs.py`                  | `feeds/krebs-products.xml`          |
| Dark Reading        | `filter_rss_darkreading.py`            | `feeds/darkreading-products.xml`    |

---

## 📁 Repository Structure

```
Curated-RSS-Feeds/
├── .github/workflows/              # GitHub Actions workflows
│   ├── rss-filter-bleeping.yml
│   ├── rss-filter-cisa.yml
│   ├── rss-filter-hackernews.yml
│   ├── rss-filter-krebs.yml
│   └── rss-filter-darkreading.yml
├── feeds/                          # Generated RSS feed outputs
│   ├── hackernews-products.xml
│   ├── cisa-products.xml
│   ├── bleeping-products.xml
│   ├── krebs-products.xml
│   └── darkreading-products.xml
├── filter_rss_hackernews.py        # HackerNews RSS filter
├── filter_rss_cisa.py              # CISA advisories RSS filter
├── filter_rss_bleeping.py          # BleepingComputer RSS filter
├── filter_rss_krebs.py             # Krebs on Security RSS filter
├── filter_rss_darkreading.py       # DarkReading RSS filter
├── check_acknowledgments.py        # Acknowledgment monitoring script
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── LICENSE                         # MIT License
└── .gitignore                      # Git ignore rules
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

