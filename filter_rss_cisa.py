import feedparser, os, json, requests
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime
import re
import base64
import time
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/New_York")
except ImportError:
    TZ = None

SOURCE_FEED = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".seen_entries_cisa.json")

# JIRA Configuration with error handling
try:
    JIRA_URL = os.environ["JIRA_URL"]
    JIRA_EMAIL = os.environ["JIRA_EMAIL"]
    JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]
    JIRA_EPIC_KEY = os.environ["JIRA_EPIC_KEY"]
    JIRA_PROJECT_KEY = os.environ["JIRA_PROJECT_KEY"]
    print(f"✅ JIRA configuration loaded - URL: {JIRA_URL}, Email: {JIRA_EMAIL}, Epic: {JIRA_EPIC_KEY}, Project: {JIRA_PROJECT_KEY}")
except KeyError as e:
    print(f"❌ Missing JIRA environment variable: {e}")
    JIRA_URL = JIRA_EMAIL = JIRA_API_TOKEN = JIRA_EPIC_KEY = JIRA_PROJECT_KEY = None

# Product keywords to monitor for security threats
# Add specific products, technologies, or services your organization uses
# Examples: "microsoft", "aws", "github", "palo alto", "crowdstrike", "1password"
PRODUCT_KEYWORDS = [
]

# Threat keywords that indicate security vulnerabilities or incidents
# Add security threat terms that will trigger alerts for your organization
# Examples: "cve", "vulnerability", "exploit", "breach", "malware", "ransomware", "zero-day", "apt", "supply chain"
THREAT_KEYWORDS = [
]

# Other keywords that might be relevant to your organization
# Add company names, industry-specific terms, or other relevant keywords
# Examples: "healthcare", "finance", "retail", "manufacturing", "education"
OTHER_KEYWORDS = [
]

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")

if SLACK_BOT_TOKEN and SLACK_CHANNEL_ID:
    print(f"✅ Slack configuration loaded - Channel: {SLACK_CHANNEL_ID}")
else:
    print(f"⚠️ Slack configuration incomplete - Token: {'✅' if SLACK_BOT_TOKEN else '❌'}, Channel: {'✅' if SLACK_CHANNEL_ID else '❌'}")

print(f"📁 Cache file path: {CACHE_FILE}")

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        seen_links = set(json.load(f))
    print(f"📋 Loaded {len(seen_links)} previously seen entries from cache")
else:
    seen_links = set()
    print("📋 No cache file found, starting fresh")

print(f"🌐 Fetching RSS feed from: {SOURCE_FEED}")
parsed = feedparser.parse(SOURCE_FEED)
print(f"📰 Found {len(parsed.entries)} total entries in RSS feed")

output_dir = os.path.join(os.path.dirname(__file__), "feeds")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "cisa-products.xml")

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")
SubElement(channel, "title").text = "Filtered - CISA Advisories"
SubElement(channel, "link").text = SOURCE_FEED
SubElement(channel, "description").text = "Filtered CISA advisories for Arcadia-relevant threats"

new_links = set()
matched_entries = []

print(f"🔍 Checking {len(parsed.entries)} entries for matches...")

for entry in parsed.entries:
    # Exclude all ICS-related advisories
    if "/ics" in entry.link:
        continue

    combined = (str(getattr(entry, 'title', '')) + ' ' + str(getattr(entry, 'description', ''))).lower()

    if (
        (any(p.lower() in combined for p in PRODUCT_KEYWORDS) and any(t.lower() in combined for t in THREAT_KEYWORDS))
        or (any(t.lower() in combined for t in THREAT_KEYWORDS) and any(c.lower() in combined for c in OTHER_KEYWORDS))
        or (any(p.lower() in combined for p in PRODUCT_KEYWORDS) and any(t.lower() in combined for t in THREAT_KEYWORDS) and any(c.lower() in combined for c in OTHER_KEYWORDS))
    ):
        print(f"✅ Found matching entry: {entry.title[:50]}...")
        if entry.link not in seen_links:
            matched_entries.append(entry)
            new_links.add(entry.link)
            print(f"🆕 New entry - will create ticket and send notification")
        else:
            print(f"📋 Entry already seen - skipping notification")

        item = SubElement(channel, "item")
        SubElement(item, "title").text = str(getattr(entry, 'title', ''))
        SubElement(item, "link").text = str(getattr(entry, 'link', ''))
        SubElement(item, "description").text = str(getattr(entry, 'description', ''))
        SubElement(item, "pubDate").text = str(getattr(entry, 'published', ''))

print(f"📊 Summary: {len(matched_entries)} new entries to process, {len(new_links)} new links")

with open(output_path, "wb") as f:
    f.write(tostring(rss, encoding="utf-8"))

def get_reactions(ts):
    url = "https://slack.com/api/reactions.get"
    params = {
        "channel": SLACK_CHANNEL_ID,
        "timestamp": ts
    }
    resp = requests.get(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}, params=params)
    return resp.json().get("message", {}).get("reactions", [])

def get_user_info(user_id):
    url = "https://slack.com/api/users.info"
    params = {"user": user_id}
    resp = requests.get(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}, params=params)
    return resp.json().get("user", {})

def get_jira_account_id(email):
    url = f"{JIRA_URL}/rest/api/3/user/search"
    params = {"query": email}
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
        "Accept": "application/json"
    }
    resp = requests.get(url, headers=headers, params=params)
    users = resp.json()
    if users and isinstance(users, list):
        return users[0].get("accountId")
    return None

def assign_jira_ticket(ticket_key, slack_email, slack_username):
    account_id = get_jira_account_id(slack_email) if slack_email else None
    if not account_id:
        print(f"❌ Could not find JIRA accountId for {slack_email or slack_username}")
        return
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {"accountId": account_id}
    resp = requests.put(f"{JIRA_URL}/rest/api/3/issue/{ticket_key}/assignee", headers=headers, json=data)
    if resp.status_code == 204:
        print(f"✅ Assigned JIRA ticket {ticket_key} to accountId {account_id}")
    else:
        print(f"❌ Failed to assign JIRA ticket: {resp.text}")

def post_thread_reply(ts, text):
    url = "https://slack.com/api/chat.postMessage"
    data = {
        "channel": SLACK_CHANNEL_ID,
        "thread_ts": ts,
        "text": text
    }
    resp = requests.post(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}", "Content-Type": "application/json"}, json=data)
    return resp.json()

def transition_jira_ticket_in_progress(ticket_key):
    url = f"{JIRA_URL}/rest/api/3/issue/{ticket_key}/transitions"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    resp = requests.get(url, headers=headers)
    transitions = resp.json().get("transitions", [])
    in_progress_id = None
    for t in transitions:
        if t["name"].lower() == "in progress":
            in_progress_id = t["id"]
            break
    if not in_progress_id:
        print("❌ Could not find 'In Progress' transition for this ticket.")
        return
    data = {"transition": {"id": in_progress_id}}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 204:
        print(f"✅ Transitioned JIRA ticket {ticket_key} to 'In Progress'")
    else:
        print(f"❌ Failed to transition JIRA ticket: {resp.text}")

def strip_html_tags(text):
    return re.sub(r'<[^>]+>', '', text or '')

def set_triage_started_field(ticket_key):
    field_id = "customfield_10684"
    if TZ:
        now_iso = datetime.now(TZ).isoformat()
    else:
        now_iso = datetime.utcnow().isoformat() + 'Z'
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "fields": {
            field_id: now_iso
        }
    }
    resp = requests.put(f"{JIRA_URL}/rest/api/3/issue/{ticket_key}", headers=headers, json=data)
    print(f"[DEBUG] Set triage started field: {resp.status_code} {resp.text}")

def monitor_for_thumbs_up(ts, ticket_key):
    print("Polling for thumbs up reactions on alert message (timeout: 1 minute)...")
    acknowledged = False
    start_time = time.time()
    timeout = 60  # 1 minute
    
    while not acknowledged and (time.time() - start_time) < timeout:
        reactions = get_reactions(ts)
        for reaction in reactions:
            if reaction["name"].startswith("thumbsup") or reaction["name"].startswith("+1") or reaction["name"].startswith("thumbs_up"):
                users = reaction.get("users", [])
                if users:
                    first_user = users[0]
                    user_info = get_user_info(first_user)
                    slack_username = user_info.get("name", "unknown user")
                    slack_email = user_info.get("profile", {}).get("email", None)
                    print(f"👍 Thumbs up detected from {slack_username} ({slack_email})! Posting acknowledgment in thread and locking assignment...")
                    post_thread_reply(ts, f"Under review and acknowledged by <@{first_user}> :white_check_mark:")
                    assign_jira_ticket(ticket_key, slack_email, slack_username)
                    set_triage_started_field(ticket_key)
                    transition_jira_ticket_in_progress(ticket_key)
                    acknowledged = True
                    break
        if not acknowledged:
            time.sleep(5)
    
    if not acknowledged:
        print("⏰ Timeout reached - no thumbs up detected within 1 minute")

def post_to_slack(entry, ticket_key=None):
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        return
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    message_parts = []
    message_parts.append(f"🛡️ CISA")
    message_parts.append(f"Title: {getattr(entry, 'title', '')}")
    if ticket_key:
        jira_url = f"{JIRA_URL}/browse/{ticket_key}"
        message_parts.append(f"JIRA Ticket: <{jira_url}|{ticket_key}>")
    text = "\n".join(message_parts)
    msg = {
        "channel": SLACK_CHANNEL_ID,
        "text": text
    }
    resp = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=msg)
    ts = resp.json().get("ts")
    if ts and ticket_key:
        monitor_for_thumbs_up(ts, ticket_key)

def create_jira_ticket(entry):
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_EPIC_KEY]):
        print("JIRA configuration incomplete. Skipping ticket creation.")
        return None
    title = entry.title.strip()
    if len(title) > 255:
        title = title[:252] + "..."
    clean_description = strip_html_tags(getattr(entry, 'description', ''))
    
    # Create a proper summary by truncating to reasonable length
    summary_text = clean_description.strip()
    if len(summary_text) > 500:
        # Truncate to 500 characters and try to end at a sentence boundary
        truncated = summary_text[:500]
        last_period = truncated.rfind('.')
        last_exclamation = truncated.rfind('!')
        last_question = truncated.rfind('?')
        
        # Find the last sentence ending
        last_sentence_end = max(last_period, last_exclamation, last_question)
        if last_sentence_end > 400:  # Only use sentence boundary if it's not too early
            summary_text = truncated[:last_sentence_end + 1]
        else:
            summary_text = truncated + "..."
    
    description = {
        "version": 1,
        "type": "doc",
        "content": [
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Security Alert Details"}]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": "Source: CISA Advisories RSS Feed"},
                {"type": "hardBreak"},
                {"type": "text", "text": f"Published: {getattr(entry, 'published', '')}"},
                {"type": "hardBreak"},
                {"type": "text", "text": f"Link: {entry.link}"}
            ]},
            {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Summary"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": summary_text}]},
            {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Keywords Detected"}]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": "Products: "},
                {"type": "text", "text": ", ".join([kw for kw in PRODUCT_KEYWORDS if kw.lower() in (entry.title + ' ' + clean_description).lower()])}
            ]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": "Threats: "},
                {"type": "text", "text": ", ".join([kw for kw in THREAT_KEYWORDS if kw.lower() in (entry.title + ' ' + clean_description).lower()])}
            ]},
            {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Customers: "}]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": ", ".join([kw for kw in OTHER_KEYWORDS if kw.lower() in (entry.title + ' ' + clean_description).lower()])}
            ]},
            {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Action Required"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": "Please review this security alert and determine if any action is required for our environment."}]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": "---"},
                {"type": "hardBreak"},
                {"type": "text", "text": f"This ticket was automatically created by the RSS filter script on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
            ]}
        ]
    }
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    issue_data = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": title,
            "description": description,
            "issuetype": {"name": "Sub-task"},
            "parent": {"key": JIRA_EPIC_KEY},
            "priority": {"name": "Medium"},
            "labels": ["security-alert", "rss-feed", "cisa", "auto-generated", "cti"]
        }
    }
    try:
        response = requests.post(f"{JIRA_URL}/rest/api/3/issue", headers=headers, json=issue_data)
        if response.status_code == 201:
            issue_key = response.json().get("key")
            print(f"✅ Created JIRA ticket: {issue_key}")
            return issue_key
        else:
            print(f"❌ Failed to create JIRA ticket. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating JIRA ticket: {str(e)}")
        return None

def process_and_notify(entries):
    for entry in entries:
        ticket_key = create_jira_ticket(entry)
        post_to_slack(entry, ticket_key)

if matched_entries:
    process_and_notify(matched_entries)

if new_links:
    seen_links.update(new_links)
    with open(CACHE_FILE, "w") as f:
        json.dump(list(seen_links), f)

