# Images Directory

This directory contains screenshots and images for the README documentation.

## Required Images

### immediate-acknowledgment.png
**Description**: Screenshot showing immediate acknowledgment during RSS script execution
**Content**: 
- Initial security alert from Security Team Bot (DarkReading alert with JIRA ticket)
- Thumbs up reaction from user (Taiga Walker) within 1 minute
- Bot acknowledgment confirmation with user mention and checkmark
- Timestamps showing quick acknowledgment (within 1 minute)

**How to add**: 
1. Take a screenshot of the Slack thread showing immediate acknowledgment
2. Save as `immediate-acknowledgment.png` in this directory
3. Ensure the image shows the alert and acknowledgment with timestamps

### acknowledgment-workflow.png
**Description**: Screenshot showing delayed acknowledgment handled by check_acknowledgments.py
**Content**: 
- Initial security alert from Security Team Bot (Krebs alert with JIRA ticket)
- Bot confirmation of JIRA ticket creation
- Thumbs up reaction from user (Taiga Walker) after RSS script timeout
- Bot acknowledgment confirmation with user mention and checkmark

**How to add**: 
1. Take a screenshot of the Slack thread showing the complete delayed workflow
2. Save as `acknowledgment-workflow.png` in this directory
3. Ensure the image shows the full thread with all messages and reactions

## Image Guidelines

- Use PNG format for screenshots
- Keep file sizes reasonable (< 1MB)
- Ensure text is readable
- Redact sensitive information (JIRA ticket numbers, etc.) if needed
- Use descriptive filenames
- Include timestamps to show timing differences between scenarios 