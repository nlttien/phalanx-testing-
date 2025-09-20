import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from browser_manager import BrowserManager

load_dotenv()

class SheetsEditHistoryCapture:
    def __init__(self, sheet_url, cdp_port=9222, profile_name="Default"):
        self.sheet_url = sheet_url
        self.history_data = {}
        self.browser_manager = BrowserManager(cdp_port, debug=True)
        self.profile_name = profile_name
    
    async def check_cdp_connection(self):
        return await self.browser_manager.check_cdp_connection()
    
    async def setup_browser(self):
        try:
            success = await self.browser_manager.setup_browser()
            if success:
                print("✅ Browser setup completed successfully")
                return True
            else:
                return False
        except Exception as e:
            return False
    
    @property
    def page(self):
        """Get page from browser manager"""
        return self.browser_manager.get_page()
    
    @property 
    def browser(self):
        """Get browser from browser manager"""
        return self.browser_manager.get_browser()
    
    @property
    def context(self):
        """Get context from browser manager"""
        return self.browser_manager.get_context()
    
    async def select_cell_using_name_box(self, cell_reference):
        try:
            await self.page.wait_for_timeout(2000)
            
            name_box_selectors = [
                'input.waffle-name-box',
                '#t-name-box',
                'input[class*="waffle-name-box"]',
                'input[id*="name-box"]',
                '.jfk-textinput.waffle-name-box',
                '[data-tooltip*="Name box"]',
                'input[placeholder*="A1"]'
            ]
            
            name_box = None
            for selector in name_box_selectors:
                try:
                    name_box = await self.page.wait_for_selector(selector, timeout=5000)
                    if name_box:
                        print(f"Found name box with selector: {selector}")
                        break
                except:
                    continue
            
            if not name_box:
                print("Could not find name box input")
                return False
            
            # Make sure name box is visible and clickable
            await name_box.scroll_into_view_if_needed()
            
            # Clear and enter cell reference
            await name_box.click()
            await self.page.wait_for_timeout(500)
            
            # Select all and clear
            await self.page.keyboard.press('Control+a')
            await self.page.wait_for_timeout(200)
            
            # Type the cell reference
            await name_box.type(cell_reference)
            await self.page.wait_for_timeout(500)
            
            # Press Enter to navigate to cell
            await self.page.keyboard.press('Enter')
            
            # Wait for cell to be selected
            await self.page.wait_for_timeout(3000)
            
            # Verify cell is selected by checking if name box shows our cell reference
            try:
                current_value = await name_box.input_value()
                if cell_reference.upper() in current_value.upper():
                    return True
                else:
                    print(f"Name box shows {current_value}, expected {cell_reference}")
            except:
                print("Could not verify name box value")
            
            print(f"Cell {cell_reference} selection completed")
            return True
            
        except Exception as e:
            print(f"Error selecting cell {cell_reference}: {e}")
            return False
    
    async def right_click_selected_cell(self):
        try:
            await self.page.wait_for_timeout(1000)
            
            try:
                elements = await self.page.query_selector_all('.active-cell-border')
                if len(elements) > 0:
                    print(f"Found {len(elements)} active cell border elements")
                    await elements[0].click(button='right', force=True)
                    await self.page.wait_for_timeout(1000)
                    
                    menu_items = await self.page.query_selector_all('[role="menuitem"], .goog-menuitem, .goog-menu-item')
                    if len(menu_items) > 0:
                        print(f"✅ Context menu opened with {len(menu_items)} items")
                        return True
            except Exception as e:
                print(f"Force click failed: {e}")
            
            return False
        except Exception as e:
            print(f"Error right-clicking selected cell: {e}")
            return False
    
    async def click_show_edit_history(self):
        try:
            # Look for edit history options
            edit_history_selectors = [
                'text="Show edit history"',
                'text="Hiển thị lịch sử chỉnh sửa"',  # Vietnamese
                'text="View edit history"',
                '*:has-text("edit history")',
                '*:has-text("lịch sử")',
                '[role="menuitem"]:has-text("history")',
                '[role="menuitem"]:has-text("lịch sử")'
            ]
            
            for selector in edit_history_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        print(f"Found edit history option with selector: {selector}")
                        await element.click()
                        await self.page.wait_for_timeout(3000)
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"Error clicking show edit history: {e}")
            return False
    
    async def extract_edit_history_data(self):
        try:
            # Look for the blame view content
            blame_view_selector = '.docs-blameview-content'
            blame_view = await self.page.wait_for_selector(blame_view_selector, timeout=5000)
            
            if not blame_view:
                return "", ""
            
            timestamp = ""
            timestamp_selectors = [
                '.docs-blameview-timestamp',
                '.docs-blameview-authortimestamp .docs-blameview-timestamp'
            ]
            
            for selector in timestamp_selectors:
                try:
                    timestamp_element = await blame_view.query_selector(selector)
                    if timestamp_element:
                        timestamp = await timestamp_element.inner_text()
                        print(f"Found timestamp: {timestamp}")
                        break
                except:
                    continue
            
            content = ""
            content_selectors = [
                '.docs-blameview-value-content',
                '.docs-blameview-valuecontainer .docs-blameview-value-content'
            ]
            
            for selector in content_selectors:
                try:
                    content_element = await blame_view.query_selector(selector)
                    if content_element:
                        content = await content_element.inner_text()
                        print(f"Found content: {content}")
                        break
                except:
                    continue
            
            if not content and not timestamp:
                all_text = await blame_view.inner_text()
                print(f"Blame view full text: {all_text}")
                
                lines = all_text.split('\n')
                for line in lines:
                    if any(time_indicator in line for time_indicator in [':', 'tháng', 'AM', 'PM', 'ago']):
                        if not timestamp:
                            timestamp = line.strip()
                    elif 'thay thế' in line.lower() or 'replaced' in line.lower():
                        if not content:
                            content = line.strip()
            
            return content.strip(), timestamp.strip()
            
        except Exception as e:
            print(f"Error extracting edit history data: {e}")
            return "", ""
    
    async def capture_cell_edit_history(self, cell_reference):
        try:
            if not await self.select_cell_using_name_box(cell_reference):
                return "", ""
            
            if not await self.right_click_selected_cell():
                return "", ""
            
            if not await self.click_show_edit_history():
                return "", ""
            
            content, timestamp = await self.extract_edit_history_data()
            
            return content, timestamp
            
        except Exception as e:
            print(f"Error capturing edit history for {cell_reference}: {e}")
            return "", ""
    
    async def capture_all_history(self):
        try:
            # Setup browser with enhanced manager
            if not await self.setup_browser():
                print("Failed to setup browser")
                return
            
            if not self.browser_manager.is_browser_ready():
                print("Browser is not ready")
                return
            
            try:
                # Navigate using enhanced navigation
                success = await self.browser_manager.navigate_to_url(self.sheet_url, 8000)
                if not success:
                    print("Failed to navigate to sheet")
                    return
                    
                await self.browser_manager.take_screenshot("sheet_loaded", "Google Sheets loaded")
            except Exception as e:
                print(f"Error navigating to sheet: {e}")
                return
            
            # Capture D2 edit history
            try:
                print("📋 Capturing D2 cell edit history...")
                d2_content, d2_timestamp = await self.capture_cell_edit_history("D2")
                if d2_content:
                    print(f"✅ D2 Content: {d2_content}")
                else:
                    print("⚠️ No D2 content found")
            except Exception as e:
                print(f"Error capturing D2 history: {e}")
                d2_content, d2_timestamp = "", ""
            
            # Wait between operations
            await self.page.wait_for_timeout(3000)
            
            # Capture D7 edit history
            try:
                print("📋 Capturing D7 cell edit history...")
                d7_content, d7_timestamp = await self.capture_cell_edit_history("D7")
                if d7_content:
                    print(f"✅ D7 Content: {d7_content}")
                else:
                    print("⚠️ No D7 content found")
            except Exception as e:
                print(f"Error capturing D7 history: {e}")
                d7_content, d7_timestamp = "", ""
            
            # Store results with enhanced data structure
            self.history_data = {
                "content_prev": d2_content or "No previous content found",
                "timestamp_prev": d2_timestamp or "No timestamp found",
                "requirements_prev": d7_content or "No previous requirements found",
                "requirements_timestamp_prev": d7_timestamp or "No timestamp found",
                "capture_date": datetime.now().isoformat(),
                "method": "enhanced_playwright_automation",
                "session_id": self.browser_manager.session_id,
                "sheet_url": self.sheet_url
            }
            
            # Log final results
            print("\n📊 CAPTURE RESULTS:")
            print("=" * 50)
            for key, value in self.history_data.items():
                print(f"{key}: {value}")
            print("=" * 50)
            
            # Take final screenshot only
            await self.browser_manager.take_screenshot("capture_completed", "Edit history capture completed")
            
        except Exception as e:
            print(f"Error in capture process: {e}")
        
        finally:
            await self.browser_manager.cleanup_browser(keep_browser_open=True)
    
    def save_history_data(self, filename=None):
        try:
            if filename is None:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                data_dir = os.path.join(os.path.dirname(current_dir), "data")
                filename = os.path.join(data_dir, "history.json")
            
            data_dir = os.path.dirname(filename)
            if data_dir:
                os.makedirs(data_dir, exist_ok=True)
                print(f"📁 Created/verified data directory: {data_dir}")
            
            # Save with pretty formatting
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                print(f"✅ File created successfully - Size: {file_size} bytes")
                return True
            else:
                print("File was not created")
                return False
            
        except Exception as e:
            print(f"Error saving history data: {e}")
            print(f"Attempted path: {filename}")
            return False

async def main():
    sheet_url = os.getenv('SHEET_URL', "https://docs.google.com/spreadsheets/d/1lNsIW2A1gmurYZ-DJt65xuX_yEsxyvoqPx84Q2B8rEM/edit?gid=0#gid=0")
    
    if not sheet_url or sheet_url == "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit":
        print("No valid sheet URL found")
        return
    
    print(f"📋 Using sheet URL from environment: {sheet_url}")
    
    # Initialize capture with enhanced browser manager
    capture = SheetsEditHistoryCapture(sheet_url)
    
    try:
        # Check CDP connection first
        cdp_available = await capture.check_cdp_connection()
        if cdp_available:
            print("🔗 Connection priority: Using existing browser via CDP")
        else:
            print("🚀 Connection priority: Starting new persistent browser")
        
        # Run the capture process
        await capture.capture_all_history()
        
        # Save results
        success = capture.save_history_data()
        
        if success:
            print("\n✅ Task completed successfully!")
        else:
            print("\nTask completed with errors")
            
    except KeyboardInterrupt:
        print("\n⏹️ Script interrupted by user")
        await capture.browser_manager.cleanup_browser(keep_browser_open=True)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        await capture.browser_manager.cleanup_browser(keep_browser_open=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        print("👋 Goodbye!")