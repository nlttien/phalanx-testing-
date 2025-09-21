# Quick Start - Level 1: Read Google Sheets

Hướng dẫn nhanh để chạy Level 1 - đọc dữ liệu từ Google Sheets.

## 🎯 Mục đích
Level 1 sẽ:
- Kết nối với Google Sheets
- Đọc danh sách contacts/recipients 
- Lưu dữ liệu vào file JSON
- Tạo screenshots quá trình

## 🚀 Chuẩn bị

### 1. Khởi động Chrome với Remote Debugging
```bash
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
```

### 2. Đăng nhập Google Account
- Mở Chrome browser
- Đăng nhập vào Google account
- Truy cập Google Sheets

### 3. Cấu hình Sheet URL (tùy chọn)
Tạo file `.env`:
```
SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
```

## ▶️ Chạy Level 1

### Command
```bash
python l1-read-sheets.py
```

### Output mẫu
```
🔍 Starting Level 1: Read Sheets Data
🌐 Connecting to browser on port 9222...
✅ Browser connected successfully
📊 Navigating to Google Sheets...
✅ Sheet loaded successfully
🔍 Reading contact data...
✅ Found 5 contacts in sheet:
   - Contact 1: john@example.com
   - Contact 2: jane@example.com
   - Contact 3: bob@example.com
📁 Saving data to: data/level1_contacts.json
✅ Level 1 completed successfully!
```

## 📊 Kết quả Level 1

### Files được tạo
```
data/
└── level1_contacts.json    # Dữ liệu contacts đã đọc

progress/
└── l1_session_20250921_143022/
    ├── browser_connected.png
    ├── sheet_loaded.png
    ├── contacts_found.png
    └── data_extracted.png
```

### Cấu trúc dữ liệu trong level1_contacts.json
```json
{
  "level1_execution": {
    "success": true,
    "timestamp": "2025-09-21T14:30:22",
    "contacts_found": 5,
    "extraction_method": "sheets_ui"
  },
  "recipient_contact_data": [
    {
      "email": "john@example.com",
      "name": "John Doe",
      "row_number": 2
    },
    {
      "email": "jane@example.com", 
      "name": "Jane Smith",
      "row_number": 3
    }
  ]
}
```

## 🔧 Troubleshooting Level 1

### ❌ "Could not connect to browser"
**Nguyên nhân**: Chrome không chạy remote debugging hoặc port sai

**Giải pháp**:
```bash
# Đóng tất cả Chrome processes
taskkill /f /im chrome.exe

# Khởi động lại Chrome với remote debugging
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
```

### ❌ "Sheet URL not found" 
**Nguyên nhân**: SHEET_URL không được cấu hình hoặc sai

**Giải pháp**:
1. Tạo file `.env` với SHEET_URL đúng
2. Hoặc sửa trực tiếp trong script:
```python
sheet_url = "https://docs.google.com/spreadsheets/d/YOUR_ACTUAL_SHEET_ID/edit"
```

### ❌ "Access denied to sheet"
**Nguyên nhân**: Không có quyền truy cập sheet hoặc chưa đăng nhập

**Giải pháp**:
1. Đảm bảo đăng nhập đúng Google account trong Chrome
2. Kiểm tra sheet có public hoặc shared với account
3. Thử mở sheet manual trong Chrome trước

### ❌ "No contacts found"
**Nguyên nhân**: Sheet không có dữ liệu hoặc format không đúng

**Giải pháp**:
1. Kiểm tra sheet có dữ liệu ở cột A (email) và B (name)
2. Đảm bảo header ở row 1
3. Dữ liệu bắt đầu từ row 2

## ✅ Kiểm tra thành công

### Level 1 chạy thành công khi:
- [ ] Console hiển thị "✅ Level 1 completed successfully"
- [ ] File `data/level1_contacts.json` được tạo
- [ ] File JSON chứa danh sách contacts hợp lệ
- [ ] Screenshots trong folder `progress/l1_session_*/`
- [ ] Không có error messages trong console

### Dữ liệu hợp lệ khi:
- [ ] JSON file có structure đúng
- [ ] `recipient_contact_data` array có ít nhất 1 contact
- [ ] Mỗi contact có `email`, `name`, `row_number`
- [ ] `level1_execution.success = true`

## 🔄 Sử dụng dữ liệu Level 1

Dữ liệu từ Level 1 sẽ được sử dụng bởi:
- **Level 2**: Đọc edit history cho từng contact
- **Level 3**: Gửi email cho từng contact  
- **Level 4**: Cập nhật status vào sheet

## 💡 Tips Level 1

1. **Đảm bảo sheet format đúng**:
   ```
   Row 1: Email | Name | Other columns...
   Row 2: john@example.com | John Doe | ...
   Row 3: jane@example.com | Jane Smith | ...
   ```

2. **Kiểm tra permissions**: Mở sheet manual trước khi chạy script

3. **Stable internet**: Đảm bảo kết nối internet ổn định

4. **Chrome window**: Giữ Chrome window visible trong quá trình chạy

5. **Retry if needed**: Script có retry logic, nhưng có thể chạy lại nếu cần

---

## 📞 Next Steps

Sau khi Level 1 thành công:
1. ✅ Kiểm tra file `data/level1_contacts.json`
2. 🔄 Chuyển sang Level 2 (nếu cần edit history)
3. 📧 Hoặc chuyển sang Level 3 (nếu cần gửi email)
4. 📊 Cuối cùng chạy Level 4 để update results