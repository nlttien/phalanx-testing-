# 📊 Google Sheets Edit History Capture - Level 2

## 🎯 Mô tả

Level 2 automation sử dụng Playwright để tự động capture edit history từ Google Sheets thông qua UI interaction. Script sẽ:

- Kết nối tới existing Chrome browser qua CDP (Chrome DevTools Protocol)
- Navigate tới Google Sheets
- Select cells D2 và D7 using name box
- Right-click và access context menu
- Extract edit history data
- Save kết quả vào JSON file

## 🔧 Yêu cầu hệ thống

### Software Requirements
- **Python 3.11+** (recommended 3.13)
- **Google Chrome Browser** (latest version)
- **Windows 10/11** (script optimized for Windows)

### Hardware Requirements
- RAM: 4GB+ (recommended 8GB+)
- Storage: 2GB free space
- Network: Stable internet connection

## 📦 Cài đặt

### 1. Clone Repository

```bash
git clone https://github.com/nlttien/phalanx-testing-.git
cd phalanx-testing-/task
```

### 2. Tạo Python Virtual Environment

```bash
# Tạo virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate

# macOS/Linux:
source .venv/bin/activate
```

### 3. Cài đặt Dependencies

```bash
# Install required packages
pip install playwright python-dotenv aiohttp

# Install Playwright browsers
playwright install chromium

# (Optional) Install all browsers
playwright install
```

### 4. Cài đặt Environment Variables

Tạo file `.env` trong thư mục `task`:

```env
# CDP Configuration
CDP_PORT=9222
CHROME_PROFILE=Default

# Optional: Google Sheets URL override
SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

## 🚀 Sử dụng

### Method 1: Auto CDP Connection (Recommended)

1. **Start Chrome với CDP enabled:**

```bash
# Method A: Using provided batch script
start-chrome-cdp-simple.bat

# Method B: Manual command
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=.\browser_data
```

2. **Chạy automation script:**

```bash
python l2-sheets-ui-edit-history.py
```

### Method 2: Manual Browser Setup

1. Mở Chrome browser manually
2. Navigate to target Google Sheets
3. Login if required
4. Run script với existing browser:

```bash
python l2-sheets-ui-edit-history.py
```

## 📁 File Structure

```
task/
├── l2-sheets-ui-edit-history.py    # Main automation script
├── README_LEVEL2.md                # This documentation
├── .env                            # Environment configuration
├── start-chrome-cdp-simple.bat     # Chrome CDP launcher
├── browser_data/                   # Chrome user data directory
├── data/                           # Output data directory
│   └── history.json               # Captured edit history
└── debug_*.png                    # Debug screenshots
```

## ⚙️ Configuration Options

### CDP Settings

```python
# In script or .env file
CDP_PORT = 9222              # Chrome DevTools Protocol port
CHROME_PROFILE = "Default"   # Chrome profile name
```

### Target Cells

```python
# Default cells to capture
CELLS = ["D2", "D7"]  # Content và Requirements cells
```

### Output Format

Kết quả được save trong `../data/history.json`:

```json
{
  "content_prev": "Previous content from D2",
  "timestamp_prev": "2025-09-20T10:30:00",
  "requirements_prev": "Previous requirements from D7", 
  "requirements_timestamp_prev": "2025-09-20T10:30:00",
  "capture_date": "2025-09-20T11:00:00.123456",
  "method": "playwright_name_box_selection"
}
```

## 🔍 Troubleshooting

### Chrome Connection Issues

**Problem:** `No browser found on CDP port 9222`

**Solutions:**
1. Ensure Chrome is started with `--remote-debugging-port=9222`
2. Check if port 9222 is available: `netstat -an | findstr 9222`
3. Try different port in `.env` file
4. Close all Chrome instances and restart

**Problem:** `'list' object has no attribute 'pages'`

**Solutions:**
1. Restart Chrome with CDP
2. Ensure at least one tab is open
3. Check Chrome version compatibility

### Element Selection Issues

**Problem:** `Could not find name box input`

**Solutions:**
1. Ensure Google Sheets is fully loaded
2. Try refreshing the page
3. Check for UI language differences
4. Verify Sheets permissions

**Problem:** `Context menu not opening`

**Solutions:**
1. Try keyboard shortcut method (Shift+F10)
2. Ensure cell is properly selected
3. Check for UI overlays blocking interaction
4. Verify Google Sheets edit permissions

### Screenshot Debugging

Script tạo debug screenshots để troubleshoot:

- `debug_sheet_loaded.png` - Sheets page after loading
- `debug_cell_*_selected.png` - Cell selection verification
- `debug_before_right_click.png` - Before context menu
- `debug_context_menu_*.png` - Context menu states
- `debug_edit_history.png` - Edit history dialog

## 🎛️ Advanced Configuration

### Custom Selectors

Modify selectors trong script nếu Google Sheets UI changes:

```python
# Name box selectors
name_box_selectors = [
    'input.waffle-name-box',
    '#t-name-box',
    'input[class*="waffle-name-box"]'
]

# Context menu selectors  
edit_history_selectors = [
    'text="Show edit history"',
    'text="Hiển thị lịch sử chỉnh sửa"'
]
```

### Timeout Adjustments

```python
# Adjust timeouts for slower systems
await self.page.wait_for_timeout(8000)  # Page load
await self.page.wait_for_selector(selector, timeout=10000)  # Element wait
```

### Multi-language Support

Script supports Vietnamese và English:

```python
edit_history_selectors = [
    'text="Show edit history"',        # English
    'text="Hiển thị lịch sử chỉnh sửa"',  # Vietnamese
    '*:has-text("edit history")',
    '*:has-text("lịch sử")'
]
```

## 🔒 Security Notes

1. **Browser Data:** Script sử dụng persistent browser data directory
2. **Credentials:** Google login session được preserve
3. **Network:** All traffic goes through normal Chrome browser
4. **Data:** Edit history data stored locally in JSON format

## 📞 Support

### Common Issues
- Chrome compatibility: Ensure latest Chrome version
- Permission issues: Run as Administrator if needed
- Port conflicts: Change CDP_PORT in .env
- Network issues: Check firewall and proxy settings

### Debug Mode
Set debug flags trong script:

```python
# Enable verbose logging
DEBUG = True
SCREENSHOT_ALL_STEPS = True
SAVE_HTML_SNAPSHOTS = True
```

### Performance Optimization

For slower systems:

```python
# Increase timeouts
LOAD_TIMEOUT = 15000
INTERACTION_TIMEOUT = 5000

# Reduce screenshot frequency
SCREENSHOT_ENABLED = False
```

## 🔄 Updates và Maintenance

### Google Sheets UI Changes
Nếu Google Sheets thay đổi UI:

1. Update selectors trong script
2. Check debug screenshots
3. Test with different browsers/versions
4. Update documentation

### Script Updates
```bash
# Update dependencies
pip install --upgrade playwright python-dotenv aiohttp

# Update Playwright browsers
playwright install --upgrade
```

## 📋 Checklist trước khi Deploy

- [ ] Python 3.11+ installed
- [ ] Virtual environment created và activated
- [ ] All dependencies installed
- [ ] Chrome browser available
- [ ] .env file configured
- [ ] Target Google Sheets accessible
- [ ] CDP port available (9222)
- [ ] Write permissions for output directory
- [ ] Test run completed successfully

## 🏆 Success Indicators

Automation thành công khi:

✅ CDP connection established  
✅ Google Sheets loaded successfully  
✅ Cells D2 và D7 selected  
✅ Context menu opened  
✅ Edit history data extracted  
✅ JSON file saved  
✅ No resource warnings  

---

**Author:** GitHub Copilot  
**Version:** 2.0  
**Last Updated:** September 2025  
**License:** MIT