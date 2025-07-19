import os
import json
import requests
import base64
from datetime import datetime, timedelta
import time

# JIRA Configuration
JIRA_URL = os.environ.get("JIRA_URL")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")

# File to store message timestamps and ticket mappings
MAPPING_FILE = os.path.join(os.path.dirname(__file__), ".message_ticket_mappings.json")

def load_message_mappings():
    """Load existing message to ticket mappings"""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r") as f:
            return json.load(f)
    return {}

def save_message_mappings(mappings):
    """Save message to ticket mappings"""
    with open(MAPPING_FILE, "w") as f:
        json.dump(mappings, f)

def get_recent_messages():
    """Get recent messages from Slack channel"""
    url = "https://slack.com/api/conversations.history"
    params = {
        "channel": SLACK_CHANNEL_ID,
        "limit": 50  # Get last 50 messages
    }
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 200:
        return resp.json().get("messages", [])
    return []

def get_reactions(ts):
    """Get reactions for a specific message"""
    url = "https://slack.com/api/reactions.get"
    params = {
        "channel": SLACK_CHANNEL_ID,
        "timestamp": ts
    }
    resp = requests.get(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}, params=params)
    return resp.json().get("message", {}).get("reactions", [])

def get_user_info(user_id):
    """Get user information from Slack"""
    url = "https://slack.com/api/users.info"
    params = {"user": user_id}
    resp = requests.get(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}, params=params)
    return resp.json().get("user", {})

def get_jira_account_id(email):
    """Get JIRA account ID for email"""
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
    """Assign JIRA ticket to user"""
    account_id = get_jira_account_id(slack_email) if slack_email else None
    if not account_id:
        print(f"❌ Could not find JIRA accountId for {slack_email or slack_username}")
        return False
    
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{JIRA_EMAIL}:{JIRA_API_TOKEN}'.encode()).decode()}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {"accountId": account_id}
    resp = requests.put(f"{JIRA_URL}/rest/api/3/issue/{ticket_key}/assignee", headers=headers, json=data)
    if resp.status_code == 204:
        print(f"✅ Assigned JIRA ticket {ticket_key} to accountId {account_id}")
        return True
    else:
        print(f"❌ Failed to assign JIRA ticket: {resp.text}")
        return False

def transition_jira_ticket_in_progress(ticket_key):
    """Transition JIRA ticket to In Progress"""
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
        return False
    
    data = {"transition": {"id": in_progress_id}}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 204:
        print(f"✅ Transitioned JIRA ticket {ticket_key} to 'In Progress'")
        return True
    else:
        print(f"❌ Failed to transition JIRA ticket: {resp.text}")
        return False

def post_thread_reply(ts, text):
    """Post reply in Slack thread"""
    url = "https://slack.com/api/chat.postMessage"
    data = {
        "channel": SLACK_CHANNEL_ID,
        "thread_ts": ts,
        "text": text
    }
    resp = requests.post(url, headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}", "Content-Type": "application/json"}, json=data)
    return resp.json()

def set_triage_started_field(ticket_key):
    """Set the triage started field in JIRA"""
    field_id = "customfield_10684"
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

def check_message_acknowledgments():
    """Main function to check for acknowledgments"""
    print("🔍 Checking for thumbs up acknowledgments on recent messages...")
    
    # Load existing mappings
    mappings = load_message_mappings()
    
    # Get recent messages
    messages = get_recent_messages()
    
    # Check each message for acknowledgments
    for message in messages:
        ts = message.get("ts")
        text = message.get("text", "")
        
        # Look for JIRA ticket references in the message
        if "JIRA Ticket:" in text:
            # Extract ticket key from message
            import re
            ticket_match = re.search(r'JIRA Ticket:\s*([A-Z]+-\d+)', text)
            if ticket_match:
                ticket_key = ticket_match.group(1)
                
                # Check if we've already processed this message
                if ts in mappings and mappings[ts].get("processed"):
                    continue
                
                # Check for thumbs up reactions
                reactions = get_reactions(ts)
                for reaction in reactions:
                    if reaction["name"].startswith("thumbsup") or reaction["name"].startswith("+1") or reaction["name"].startswith("thumbs_up"):
                        users = reaction.get("users", [])
                        if users:
                            first_user = users[0]
                            user_info = get_user_info(first_user)
                            slack_username = user_info.get("name", "unknown user")
                            slack_email = user_info.get("profile", {}).get("email", None)
                            
                            print(f"👍 Thumbs up detected on message {ts} for ticket {ticket_key} from {slack_username}")
                            
                            # Post acknowledgment
                            post_thread_reply(ts, f"Under review and acknowledged by <@{first_user}> :white_check_mark:")
                            
                            # Assign ticket and transition
                            assign_success = assign_jira_ticket(ticket_key, slack_email, slack_username)
                            set_triage_started_field(ticket_key)
                            transition_success = transition_jira_ticket_in_progress(ticket_key)
                            
                            # Mark as processed
                            mappings[ts] = {
                                "ticket_key": ticket_key,
                                "processed": True,
                                "acknowledged_by": slack_username,
                                "acknowledged_at": datetime.now().isoformat()
                            }
                            
                            print(f"✅ Processed acknowledgment for ticket {ticket_key}")
                            break
                
                # If no thumbs up found, mark as checked but not processed
                if ts not in mappings:
                    mappings[ts] = {
                        "ticket_key": ticket_key,
                        "processed": False,
                        "checked_at": datetime.now().isoformat()
                    }
    
    # Save updated mappings
    save_message_mappings(mappings)
    print(f"💾 Saved message mappings for {len(mappings)} messages")

if __name__ == "__main__":
    if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, SLACK_BOT_TOKEN, SLACK_CHANNEL_ID]):
        print("❌ Missing required environment variables")
        exit(1)
    
    check_message_acknowledgments() 