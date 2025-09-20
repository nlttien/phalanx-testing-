# Quick Start - Level 3 Gmail Auto Sender

## 🚀 5-Minute Setup

### Step 1: Start Chrome with CDP
```cmd
start-chrome-cdp-simple.bat
```

### Step 2: Login to Gmail
- Gmail will open automatically
- Complete login if needed

### Step 3: Test Setup
```cmd
cd task
python test-level3.py
```

Expected output:
```
✅ Level 1 data found: khoi.nguyen@phalanxco.services
✅ Level 2 data found: Previous content/requirements  
✅ Gmail URL configured
✅ Browser connected
✅ All tests passed! Ready to run Level 3
```

### Step 4: Run Level 3
```cmd
python l3-gmail-send.py
```

Expected output:
```
🚀 Starting Level 3 - Gmail Auto Sender
✅ Found browser: Chrome via CDP
✅ Loaded Level 1 data
✅ Loaded Level 2 data  
📧 Navigating to Gmail
✅ Gmail loaded successfully
✅ Compose window opened
✅ Filled To field: khoi.nguyen@phalanxco.services
✅ Filled Subject field: Don't Miss Out On This News
✅ Filled Body field
📤 Clicked Send button
✅ Send confirmation found
📸 Proof screenshot saved: ../data/sent_proof_20250920_143052.png
✅ Email sent successfully!
```

## 📧 Email Content Preview
```
To: khoi.nguyen@phalanxco.services
Subject: Don't Miss Out On This News

Dear Khoi Nguyen,

Previous version of content from D2

Previous requirements text from D7

Best regards
```

## 📁 Generated Files
- `data/sent_proof_YYYYMMDD_HHMMSS.png` - Screenshot proof
- `data/level3_send_report.json` - Detailed send report

## 🔧 Troubleshooting

**Chrome CDP not found**
```cmd
start-chrome-cdp-simple.bat
```

**Gmail not logged in**  
- Login manually in the CDP browser window

**Test failures**
```cmd
# Run previous levels first
python l1-read-sheets.py
python l2-sheets-ui-edit-history.py
```

## ✅ Success Verification
1. Check Gmail Sent folder for the email
2. Verify screenshot proof in `data/` folder
3. Review send report JSON file

## 🎯 Level 3 Complete!
Your email has been automatically composed and sent using data from Level 1 and Level 2!