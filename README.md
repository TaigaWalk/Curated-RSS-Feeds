# RSS Security Alert Filter with JIRA Integration

This script monitors multiple RSS feeds for security alerts related to specific products and threats, then creates JIRA tickets with Slack notifications and automated acknowledgment workflows.

## Features

- **Multi-Source RSS Filtering**: Monitors BleepingComputer, CISA, HackerNews, Krebs, and DarkReading RSS feeds
- **Keyword Matching**: Filters entries based on customizable product and threat keywords
- **Slack Integration**: Posts formatted alerts to Slack with source, title, and JIRA ticket links
- **JIRA Integration**: Creates JIRA tickets as subtasks linked to a security epic
- **Hybrid Acknowledgment System**: 
  - **Immediate Response**: RSS scripts monitor for thumbs up for 1 minute
  - **Late Catch-up**: Separate acknowledgment script catches delayed responses
  - **No Infinite Loops**: Guaranteed timeout protection
- **Ticket Status Management**: Automatically transitions tickets to "In Progress" upon acknowledgment
- **Duplicate Prevention**: Uses cache files to avoid creating duplicate tickets
- **Rate Limit Protection**: Optimized API usage to prevent rate limiting

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

### RSS Filter Scripts

Run any of the filter scripts:

```bash
python filter_rss_bleeping.py
python filter_rss_cisa.py
python filter_rss_hackernews.py
python filter_rss_krebs.py
python filter_rss_darkreading.py
```

### Acknowledgment Script

Run the acknowledgment script to catch late acknowledgments:

```bash
python check_acknowledgments.py
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

### 3. Hybrid Acknowledgment Workflow
6. **Immediate Monitoring**: RSS script monitors for thumbs up reactions for exactly 1 minute
7. **Timeout Protection**: If no acknowledgment within 1 minute, script finishes safely
8. **Late Catch-up**: Separate acknowledgment script checks recent messages for missed acknowledgments
9. **User Assignment**: First person to react gets assigned the JIRA ticket (using their Slack email)
10. **Status Update**: Ticket automatically transitions to "In Progress"
11. **Confirmation**: Bot posts acknowledgment message in the Slack thread
12. **Cache Update**: Updates cache files to prevent duplicate processing

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
- **💻 HackerNews** - Computer emoji for tech news
- **🔍 KrebsOnSecurity** - Magnifying glass emoji for investigative journalism
- **🌑 Dark Reading** - Moon emoji for "dark" security news

The ticket number is a clickable link that takes you directly to the JIRA ticket.

## Acknowledgment Workflow

### Immediate Response (RSS Scripts)
1. **Alert Posted**: Security alert appears in Slack with JIRA ticket link
2. **1-Minute Window**: RSS script monitors for thumbs up reactions
3. **Quick Acknowledgment**: If thumbs up detected within 1 minute:
   - First person to react gets assigned the JIRA ticket
   - Ticket automatically transitions to "In Progress"
   - Bot posts acknowledgment message in the thread
4. **Safe Timeout**: If no acknowledgment within 1 minute, script finishes

### Late Catch-up (Acknowledgment Script)
5. **Manual Check**: Run `check_acknowledgments.py` to check for late acknowledgments
6. **Recent Messages**: Script checks last 50 messages for JIRA ticket references
7. **Reaction Detection**: Looks for thumbs up reactions on messages with JIRA tickets
8. **Processing**: Same acknowledgment workflow as RSS scripts
9. **Cache Protection**: Prevents duplicate processing

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
- ⏰ Timeout messages when no acknowledgment is detected

## Files

### Main Scripts
- `filter_rss_bleeping.py`: BleepingComputer RSS filter
- `filter_rss_cisa.py`: CISA advisories RSS filter
- `filter_rss_hackernews.py`: HackerNews RSS filter
- `filter_rss_krebs.py`: Krebs on Security RSS filter
- `filter_rss_darkreading.py`: DarkReading RSS filter
- `check_acknowledgments.py`: Late acknowledgment processor

### Support Files
- `requirements.txt`: Python dependencies
- `.seen_entries_*.json`: Cache files for RSS entries (auto-generated)
- `.message_ticket_mappings.json`: Cache file for acknowledgment tracking (auto-generated)
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
- **✅ Check RSS Alert Acknowledgments** - `.github/workflows/check-acknowledgments.yml`

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
- **Timeout Protection**: RSS workflows have 1-minute timeout to prevent infinite loops

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
│   ├── rss-filter-darkreading.yml
│   └── check-acknowledgments.yml
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
├── check_acknowledgments.py        # Late acknowledgment processor
├── requirements.txt                 # Python dependencies
├── README.md                       # This file
├── LICENSE                         # MIT License
└── .gitignore                      # Git ignore rules
```

## System Architecture

### Key Improvements

✅ **No Infinite Loops**: RSS scripts have 1-minute timeout protection  
✅ **Hybrid Acknowledgment**: Immediate response + late catch-up system  
✅ **Rate Limit Safe**: Optimized API usage and timeout protection  
✅ **Duplicate Prevention**: Multiple cache systems prevent double-processing  
✅ **Manual Control**: All workflows are manual for better control  

### Workflow Timing

- **RSS Scripts**: 1-minute timeout for immediate acknowledgment
- **Acknowledgment Script**: Manual execution to catch late responses
- **No Conflicts**: Multiple RSS scripts can run simultaneously safely

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

