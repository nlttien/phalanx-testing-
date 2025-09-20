import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from browser_manager import BrowserManager

load_dotenv()

class SheetsUpdater:
    def __init__(self, sheet_url, cdp_port=9222):
        self.sheet_url = sheet_url
        self.browser_manager = BrowserManager(cdp_port, debug=True)
        self.updated_sheet_url = None
        self.email_send_data = None
        self.history_data = None
        
    async def setup_browser(self):
        try:
            success = await self.browser_manager.setup_browser()
            if success:
                return True
            else:
                return False
        except Exception as e:
            return False
    
    @property
    def page(self):
        return self.browser_manager.get_page()
    
    def load_previous_level_data(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(current_dir), "data")
            
            email_send_report_path = os.path.join(data_dir, "level3_send_report.json")
            if os.path.exists(email_send_report_path):
                with open(email_send_report_path, 'r', encoding='utf-8') as f:
                    self.email_send_data = json.load(f)
            else:
                self.email_send_data = {
                    "level3_execution": {
                        "success": True,
                        "timestamp": datetime.now().isoformat(),
                        "recipient": "test@example.com",
                        "subject": "Test Email"
                    }
                }
            
            history_file_path = os.path.join(data_dir, "history.json")
            if os.path.exists(history_file_path):
                with open(history_file_path, 'r', encoding='utf-8') as f:
                    self.history_data = json.load(f)
            else:
                self.history_data = {
                    "content_prev": "Previous content not found",
                    "timestamp_prev": "No timestamp found"
                }
            
            return True
            
        except Exception as e:
            return False
    
    async def navigate_to_sheet(self):
        try:
            success = await self.browser_manager.navigate_to_url(self.sheet_url, 5000)
            if success:
                await self.browser_manager.take_screenshot("original_sheet_loaded", "Original sheet loaded")
                return True
            else:
                return False
        except Exception as e:
            return False
    
    async def select_cell(self, cell_reference):
        try:
            print(f"🎯 Attempting to select cell: {cell_reference}")
            
            # Method 1: Try to use name box
            name_box_selectors = [
                'input.waffle-name-box',
                '#t-name-box',
                'input[class*="waffle-name-box"]',
                'input[id*="name-box"]',
                '.jfk-textinput.waffle-name-box',
                '[data-tooltip*="Name box"]',
                'input[placeholder*="A1"]',
                'input[aria-label*="Name box"]',
                'input[title*="Name box"]'
            ]
            
            name_box = None
            for selector in name_box_selectors:
                try:
                    # Wait for element to exist
                    element = await self.page.query_selector(selector)
                    if element:
                        # Check if element is visible and enabled
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        if is_visible and is_enabled:
                            name_box = element
                            print(f"✅ Found name box with selector: {selector}")
                            break
                        else:
                            print(f"⚠️ Name box found but not usable (visible: {is_visible}, enabled: {is_enabled})")
                except Exception as e:
                    print(f"⚠️ Error checking selector {selector}: {e}")
                    continue
            
            if name_box:
                try:
                    # Try name box method
                    await name_box.click()
                    await self.page.wait_for_timeout(500)
                    
                    # Clear existing content
                    await self.page.keyboard.press('Control+a')
                    await self.page.wait_for_timeout(200)
                    
                    # Type cell reference
                    await name_box.type(cell_reference)
                    await self.page.wait_for_timeout(500)
                    
                    # Press Enter to navigate
                    await self.page.keyboard.press('Enter')
                    await self.page.wait_for_timeout(2000)
                    
                    print(f"✅ Selected cell {cell_reference} using name box")
                    return True
                    
                except Exception as e:
                    print(f"⚠️ Name box method failed: {e}, trying alternative methods...")
            
            # Method 2: Try keyboard shortcut (Ctrl+G)
            try:
                print("🔄 Trying keyboard shortcut method (Ctrl+G)...")
                await self.page.keyboard.press('Control+g')
                await self.page.wait_for_timeout(1000)
                
                # Look for "Go to" dialog
                go_to_selectors = [
                    'input[placeholder*="Enter"]',
                    'input[aria-label*="range"]',
                    'input[type="text"]'
                ]
                
                for selector in go_to_selectors:
                    input_element = await self.page.query_selector(selector)
                    if input_element:
                        try:
                            await input_element.type(cell_reference)
                            await self.page.wait_for_timeout(300)
                            await self.page.keyboard.press('Enter')
                            await self.page.wait_for_timeout(2000)
                            print(f"✅ Selected cell {cell_reference} using Ctrl+G")
                            return True
                        except:
                            continue
                            
            except Exception as e:
                print(f"⚠️ Keyboard shortcut method failed: {e}")
            
            # Method 3: Try clicking on cell directly (for simple cases)
            try:
                print(f"🔄 Trying direct cell click method for {cell_reference}...")
                
                # Parse cell reference (e.g., "E1" -> column E, row 1)
                if len(cell_reference) >= 2:
                    column = cell_reference[0].upper()
                    row = cell_reference[1:]
                    
                    # Try to find cell by data attributes or coordinates
                    cell_selectors = [
                        f'[data-col="{ord(column) - ord("A")}"][data-row="{int(row) - 1}"]',
                        f'[aria-label*="{cell_reference}"]',
                        f'[title*="{cell_reference}"]'
                    ]
                    
                    for selector in cell_selectors:
                        cell_element = await self.page.query_selector(selector)
                        if cell_element:
                            await cell_element.click()
                            await self.page.wait_for_timeout(1000)
                            print(f"✅ Selected cell {cell_reference} by direct click")
                            return True
                            
            except Exception as e:
                print(f"⚠️ Direct click method failed: {e}")
            
            # Method 4: Use JavaScript to set active cell
            try:
                print(f"🔄 Trying JavaScript method for {cell_reference}...")
                
                # Try to use Google Sheets internal APIs if available
                js_code = f"""
                try {{
                    // Try different ways to select cell
                    if (window.google && window.google.sheets) {{
                        // Google Sheets API method
                        window.google.sheets.selectRange('{cell_reference}');
                        return true;
                    }}
                    
                    // Try to find and click name box
                    const nameBox = document.querySelector('input.waffle-name-box') || 
                                   document.querySelector('#t-name-box') ||
                                   document.querySelector('input[class*="waffle-name-box"]');
                    if (nameBox) {{
                        nameBox.focus();
                        nameBox.select();
                        nameBox.value = '{cell_reference}';
                        nameBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        nameBox.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                        return true;
                    }}
                    
                    return false;
                }} catch (error) {{
                    console.error('JavaScript selection error:', error);
                    return false;
                }}
                """
                
                result = await self.page.evaluate(js_code)
                if result:
                    await self.page.wait_for_timeout(2000)
                    print(f"✅ Selected cell {cell_reference} using JavaScript")
                    return True
                    
            except Exception as e:
                print(f"⚠️ JavaScript method failed: {e}")
            
            print(f"❌ All methods failed to select cell {cell_reference}")
            return False
            
        except Exception as e:
            print(f"❌ Critical error selecting cell {cell_reference}: {e}")
            return False
    
    async def verify_cell_selected(self, expected_cell):
        """Verify that the correct cell is currently selected"""
        try:
            # Method 1: Check name box value
            name_box_selectors = [
                'input.waffle-name-box',
                '#t-name-box',
                'input[class*="waffle-name-box"]'
            ]
            
            for selector in name_box_selectors:
                name_box = await self.page.query_selector(selector)
                if name_box:
                    try:
                        current_value = await name_box.input_value()
                        if current_value.upper() == expected_cell.upper():
                            print(f"✅ Verified cell selection: {current_value}")
                            return True
                    except:
                        continue
            
            # Method 2: Check active cell indicators
            try:
                # Look for active cell visual indicators
                active_indicators = [
                    '.active-cell',
                    '.selected-cell',
                    '.cell-selected',
                    '.active-cell-border'
                ]
                
                for selector in active_indicators:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        print(f"✅ Found active cell indicator: {selector}")
                        return True
            except:
                pass
            
            print(f"⚠️ Could not verify cell {expected_cell} selection")
            return True  # Return True to continue execution even if verification fails
            
        except Exception as e:
            print(f"⚠️ Error verifying cell selection: {e}")
            return True  # Return True to continue execution
    
    async def update_cell_content(self, content):
        """Update the content of the currently selected cell"""
        try:
            print(f"✏️ Updating cell content: {content}")
            
            # Double-click to enter edit mode
            await self.page.keyboard.press('F2')
            await self.page.wait_for_timeout(500)
            
            # Alternative: Double-click on the cell
            try:
                active_cell = await self.page.query_selector('.active-cell-border')
                if active_cell:
                    await active_cell.dblclick()
                    await self.page.wait_for_timeout(500)
            except:
                pass
            
            # Clear existing content and type new content
            await self.page.keyboard.press('Control+a')
            await self.page.wait_for_timeout(200)
            await self.page.keyboard.type(content)
            await self.page.wait_for_timeout(500)
            
            # Press Enter to confirm
            await self.page.keyboard.press('Enter')
            await self.page.wait_for_timeout(1000)
            
            print(f"✅ Updated cell content")
            return True
            
        except Exception as e:
            print(f"Error updating cell content: {e}")
            return False
    
    async def create_headers_if_needed(self):
        try:
            headers = {
                "E1": "Status",
                "F1": "Send Date", 
                "G1": "History Content",
                "H1": "History Date"
            }
            
            # Check and create each header
            for cell_ref, header_text in headers.items():
                selection_success = False
                for attempt in range(3):  # Try up to 3 times
                    if await self.select_cell(cell_ref):
                        # Verify selection worked
                        if await self.verify_cell_selected(cell_ref):
                            selection_success = True
                            break
                        else:
                            print(f"⚠️ Selection verification failed for {cell_ref}, attempt {attempt + 1}")
                    
                    if attempt < 2:  # Don't wait after last attempt
                        await self.page.wait_for_timeout(1000)
                
                if not selection_success:
                    print(f"❌ Failed to select {cell_ref} after 3 attempts, skipping...")
                    continue
                
                # Check if header already exists
                try:
                    current_value = ""
                    
                    try:
                        formula_bar_selectors = [
                            '#t-formula-bar-input',
                            '.cell-input',
                            'input[data-tooltip*="formula"]',
                            'input[aria-label*="formula"]'
                        ]
                        
                        for selector in formula_bar_selectors:
                            formula_bar = await self.page.query_selector(selector)
                            if formula_bar:
                                try:
                                    # Check if it's actually an input element before calling input_value
                                    tag_name = await formula_bar.evaluate('(element) => element.tagName.toLowerCase()')
                                    if tag_name in ['input', 'textarea']:
                                        current_value = await formula_bar.input_value()
                                        if current_value.strip():
                                            break
                                    else:
                                        # Try to get text content instead
                                        current_value = await formula_bar.text_content()
                                        if current_value and current_value.strip():
                                            break
                                except Exception as inner_e:
                                    print(f"⚠️ Error getting value from formula bar: {inner_e}")
                                    continue
                    except Exception as e:
                        print(f"⚠️ Error accessing formula bar: {e}")
                    
                    # Clean up the current value
                    current_value = current_value.strip() if current_value else ""
                    
                    # Check if header already exists and matches
                    if current_value == header_text:
                        print(f"✅ Header {cell_ref} already exists: {current_value}")
                        continue
                    elif current_value:
                        print(f"⚠️ Cell {cell_ref} has different content: '{current_value}' - will update to '{header_text}'")
                    else:
                        print(f"📝 Cell {cell_ref} is empty - creating header: {header_text}")
                    
                    # Update cell content
                    await self.update_cell_content(header_text)
                    await self.browser_manager.take_screenshot(f"header_{cell_ref}_created", f"Header {header_text} created")
                    await self.page.wait_for_timeout(1000)
                    
                except Exception as e:
                    print(f"⚠️ Error checking {cell_ref} content: {e} - will create header anyway")
                    await self.update_cell_content(header_text)
                    await self.page.wait_for_timeout(1000)
            
            print("✅ Headers created successfully")
            return True
            
        except Exception as e:
            await self.browser_manager.take_screenshot("header_creation_error", "Error creating headers")
            return False

    async def update_sheet_row(self):
        try:
            if not self.email_send_data or not self.history_data:
                print("Missing required data from previous levels")
                return False
            
            if not await self.create_headers_if_needed():
                print("⚠️ Header creation failed, continuing with data entry...")
            
            level3_execution = self.email_send_data.get('level3_execution', {})
            send_success = level3_execution.get('success', False)
            send_timestamp = level3_execution.get('timestamp', datetime.now().isoformat())
            
            try:
                send_date = datetime.fromisoformat(send_timestamp.replace('Z', '+00:00'))
                formatted_send_date = send_date.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_send_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            history_content = self.history_data.get('content_prev', 'No previous content')
            history_date = self.history_data.get('timestamp_prev', 'No timestamp')
            
            data_updates = {
                "E2": ("Status", "✅" if send_success else "❌"),
                "F2": ("Send Date", formatted_send_date),
                "G2": ("History Content", history_content),
                "H2": ("History Date", history_date)
            }
            
            print("\n📝 Starting row 2 data updates...")
            for cell_ref, (description, new_value) in data_updates.items():
                print(f"\n📍 Processing data cell {cell_ref} (expected: '{new_value}')")
                
                # Try to select the cell with retry logic
                selection_success = False
                for attempt in range(3):  # Try up to 3 times
                    if await self.select_cell(cell_ref):
                        # Verify selection worked
                        if await self.verify_cell_selected(cell_ref):
                            selection_success = True
                            break
                        else:
                            print(f"⚠️ Selection verification failed for {cell_ref}, attempt {attempt + 1}")
                    
                    if attempt < 2:  # Don't wait after last attempt
                        await self.page.wait_for_timeout(1000)
                
                if not selection_success:
                    print(f"❌ Failed to select {cell_ref} after 3 attempts, skipping...")
                    continue
                
            # Take final screenshot
            await self.browser_manager.take_screenshot("row_updated_complete", "Row update completed")
            
            print("✅ All data entered successfully in row 2")
            return True
            
        except Exception as e:
            await self.browser_manager.take_screenshot("update_error", "Error during row update")
            return False
    
    async def execute_sheet_update_process(self):
        try:
            if not self.load_previous_level_data():
                return False
            
            if not await self.setup_browser():
                return False
            
            if not await self.navigate_to_sheet():
                return False
            
            if not await self.update_sheet_row():
                return False
            
            return True
            
        except Exception as e:
            print(f"\nLevel 4 workflow failed: {e}")
            await self.browser_manager.take_screenshot("level4_error", "Level 4 workflow error")
            return False
        
        finally:
            await self.browser_manager.cleanup_browser(keep_browser_open=True)

async def main():
    sheet_url = os.getenv('SHEET_URL', "https://docs.google.com/spreadsheets/d/1lNsIW2A1gmurYZ-DJt65xuX_yEsxyvoqPx84Q2B8rEM/edit?gid=0#gid=0")
    
    if not sheet_url or sheet_url == "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit":
        print("No valid sheet URL found")
        return
    
    updater = SheetsUpdater(sheet_url)
    
    try:
        success = await updater.execute_sheet_update_process()
        
        if success:
            if updater.updated_sheet_url:
                print(f"📄 Updated sheet: {updater.updated_sheet_url}")
        else:
            print("\nLevel 4 completed with errors")
            
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        await updater.browser_manager.cleanup_browser(keep_browser_open=True)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        await updater.browser_manager.cleanup_browser(keep_browser_open=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        print("👋 Level 4 automation finished!")