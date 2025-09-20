import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

class SheetsEditHistoryCapture:
    def __init__(self, sheet_url, cdp_port=9222, profile_name="Default"):
        self.sheet_url = sheet_url
        self.history_data = {}
        self.cdp_port = cdp_port
        self.profile_name = profile_name
        self.browser = None  
    
    async def check_cdp_connection(self):
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:{self.cdp_port}/json/version") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Found browser: {data.get('Browser', 'Unknown')} via CDP")
                        return True
                    else:
                        return False
        except Exception as e:
            print(f"No browser found on CDP port {self.cdp_port}: {e}")
            return False
    
    async def setup_browser(self):
        try:
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.connect_over_cdp("http://localhost:9222")
            
            self.context = self.browser.contexts[0] 
            
            self.page = self.context.pages[0]
        except Exception as e:
            raise e
        
    async def navigate_to_sheet(self):
        await self.page.goto(self.sheet_url)
        
        # Wait for page to load
        await self.page.wait_for_timeout(8000)
        
        # Take screenshot for debugging
        await self.page.screenshot(path="debug_sheet_loaded.png")
    
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
                await self.page.screenshot(path="debug_no_name_box.png")
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
            
            # Take screenshot to verify selection
            await self.page.screenshot(path=f"debug_cell_{cell_reference}_selected.png")
            
            # Verify cell is selected by checking if name box shows our cell reference
            try:
                current_value = await name_box.input_value()
                if cell_reference.upper() in current_value.upper():
                    print(f"✅ Cell {cell_reference} selected successfully (name box shows: {current_value})")
                    return True
                else:
                    print(f"⚠️ Name box shows {current_value}, expected {cell_reference}")
            except:
                print("Could not verify name box value")
            
            print(f"Cell {cell_reference} selection completed")
            return True
            
        except Exception as e:
            print(f"Error selecting cell {cell_reference}: {e}")
            await self.page.screenshot(path=f"debug_select_cell_{cell_reference}_error.png")
            return False
    
    async def right_click_selected_cell(self):
        try:
            await self.page.wait_for_timeout(1000)
            
            await self.page.screenshot(path="debug_before_right_click.png")
            
            try:
                await self.page.keyboard.press('Escape')
                await self.page.wait_for_timeout(500)
                await self.page.keyboard.press('Shift+F10')
                await self.page.wait_for_timeout(2000)
                
                menu_items = await self.page.query_selector_all('[role="menuitem"], .goog-menuitem, .goog-menu-item')
                if len(menu_items) > 0:
                    print(f"✅ Context menu opened via keyboard with {len(menu_items)} items")
                    await self.page.screenshot(path="debug_context_menu_keyboard.png")
                    return True
            except Exception as e:
                print(f"Keyboard shortcut failed: {e}")
            
            try:
                await self.page.evaluate("""
                    const covers = document.querySelectorAll('.selection-border-cover');
                    covers.forEach(cover => cover.style.pointerEvents = 'none');
                """)
                
                elements = await self.page.query_selector_all('.active-cell-border')
                if len(elements) > 0:
                    print(f"Found {len(elements)} active cell border elements")
                    await elements[0].click(button='right')
                    await self.page.wait_for_timeout(2000)
                    
                    await self.page.evaluate("""
                        const covers = document.querySelectorAll('.selection-border-cover');
                        covers.forEach(cover => cover.style.pointerEvents = '');
                    """)
                    
                    menu_items = await self.page.query_selector_all('[role="menuitem"], .goog-menuitem, .goog-menu-item')
                    if len(menu_items) > 0:
                        print(f"✅ Context menu opened after bypassing cover with {len(menu_items)} items")
                        await self.page.screenshot(path="debug_context_menu_bypass.png")
                        return True
            except Exception as e:
                print(f"Bypass method failed: {e}")
            
            try:
                elements = await self.page.query_selector_all('.active-cell-border')
                if len(elements) > 0:
                    print(f"Found {len(elements)} active cell border elements")
                    await elements[0].click(button='right', force=True)
                    await self.page.wait_for_timeout(2000)
                    
                    menu_items = await self.page.query_selector_all('[role="menuitem"], .goog-menuitem, .goog-menu-item')
                    if len(menu_items) > 0:
                        print(f"✅ Context menu opened with {len(menu_items)} items")
                        await self.page.screenshot(path="debug_context_menu_success.png")
                        return True
            except Exception as e:
                print(f"Force click failed: {e}")
            
            try:
                await self.page.keyboard.press('Escape')
                await self.page.wait_for_timeout(500)
                await self.page.keyboard.press('Shift+F10')
                await self.page.wait_for_timeout(2000)
                
                menu_items = await self.page.query_selector_all('[role="menuitem"], .goog-menuitem, .goog-menu-item')
                if len(menu_items) > 0:
                    print(f"✅ Context menu opened via keyboard with {len(menu_items)} items")
                    await self.page.screenshot(path="debug_context_menu_keyboard.png")
                    return True
            except Exception as e:
                print(f"Keyboard shortcut failed: {e}")
            
            try:
                name_box = await self.page.query_selector('input.waffle-name-box')
                if name_box:
                    current_cell = await name_box.input_value()
                    print(f"Current selected cell: {current_cell}")
                
                grid_cells = await self.page.query_selector_all('.waffle-cell')
                for cell in grid_cells[:10]: 
                    try:
                        if await cell.is_visible():
                            box = await cell.bounding_box()
                            if box:
                                center_x = box['x'] + box['width'] / 2
                                center_y = box['y'] + box['height'] / 2
                                
                                await self.page.mouse.click(center_x, center_y, button='right')
                                print(f"Right-clicked at coordinates ({center_x}, {center_y})")
                                await self.page.wait_for_timeout(2000)
                                
                                menu_items = await self.page.query_selector_all('[role="menuitem"], .goog-menuitem, .goog-menu-item')
                                if len(menu_items) > 0:
                                    print(f"✅ Context menu opened via coordinates with {len(menu_items)} items")
                                    await self.page.screenshot(path="debug_context_menu_coordinates.png")
                                    return True
                                break
                    except Exception as cell_error:
                        continue
            except Exception as coord_error:
                print(f"Coordinate method failed: {coord_error}")
            
            print("Could not open context menu with any method")
            await self.page.screenshot(path="debug_right_click_failed.png")
            return False
                    
        except Exception as e:
            print(f"Error right-clicking selected cell: {e}")
            await self.page.screenshot(path="debug_right_click_error.png")
            return False
    
    async def click_show_edit_history(self):
        try:
            await self.page.screenshot(path="debug_context_menu.png")
            
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
            await self.page.screenshot(path="debug_edit_history.png")
            
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
            
            # Step 4: Extract edit history data
            content, timestamp = await self.extract_edit_history_data()
            
            print(f"Captured data for {cell_reference}:")
            print(f"  Content: {content}")
            print(f"  Timestamp: {timestamp}")
            
            return content, timestamp
            
        except Exception as e:
            print(f"Error capturing edit history for {cell_reference}: {e}")
            return "", ""
    
    async def capture_all_history(self):
        try:
            await self.setup_browser()
            
            if not hasattr(self, 'page') or not self.page:
                print("Error: Browser setup failed")
                return
            
            try:
                await self.navigate_to_sheet()
            except Exception as e:
                print(f"Error navigating to sheet: {e}")
                return
            
            try:
                d2_content, d2_timestamp = await self.capture_cell_edit_history("D2")
            except Exception as e:
                print(f"Error capturing D2 history: {e}")
                d2_content, d2_timestamp = "", ""
            
            await self.page.wait_for_timeout(3000)
            
            # Capture D7 edit history
            try:
                d7_content, d7_timestamp = await self.capture_cell_edit_history("D7")
            except Exception as e:
                print(f"Error capturing D7 history: {e}")
                d7_content, d7_timestamp = "", ""
            
            # Store results
            self.history_data = {
                "content_prev": d2_content or "No previous content found",
                "timestamp_prev": d2_timestamp or "No timestamp found",
                "requirements_prev": d7_content or "No previous requirements found",
                "requirements_timestamp_prev": d7_timestamp or "No timestamp found",
                "capture_date": datetime.now().isoformat(),
                "method": "playwright_name_box_selection"
            }
            
            for key, value in self.history_data.items():
                print(f"{key}: {value}")
            
        except Exception as e:
            print(f"Error in capture process: {e}")
            if hasattr(self, 'page'):
                await self.page.screenshot(path="error_capture.png")
        
        finally:
            await self.cleanup_browser()

    async def cleanup_browser(self):
        try:
            if hasattr(self, 'browser') and self.browser:
                print("📌 CDP connection - keeping browser open for session persistence")
            
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
                
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
    
    def save_history_data(self, filename="../data/history.json"):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            
            print(f"\nHistory data saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving history data: {e}")
            return False

async def main():
    sheet_url = os.getenv('SHEET_URL', "https://docs.google.com/spreadsheets/d/1lNsIW2A1gmurYZ-DJt65xuX_yEsxyvoqPx84Q2B8rEM/edit?gid=0#gid=0")
    
    if not sheet_url or sheet_url == "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit":
        return
    
    print(f"📋 Using sheet URL from environment: {sheet_url}")
    
    capture = SheetsEditHistoryCapture(sheet_url)
    
    cdp_available = await capture.check_cdp_connection()
    if cdp_available:
        print("Connection priority: Using existing browser via CDP")
    else:
        print("Connection priority: Starting new persistent browser")
    
    try:
        await capture.capture_all_history()
        
        success = capture.save_history_data()
        
        if success:
            print("\\n Task completed successfully!")
        else:
            print("\\n Task completed with errors")
            
    except KeyboardInterrupt:
        if hasattr(capture, 'cleanup_browser'):
            await capture.cleanup_browser()
    except Exception as e:
        if hasattr(capture, 'cleanup_browser'):
            await capture.cleanup_browser()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        print("👋 Goodbye!")