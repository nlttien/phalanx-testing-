import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class SheetsEditHistoryCapture:
    def __init__(self, sheet_url):
        self.sheet_url = sheet_url
        self.history_data = {}
    
    async def setup_browser(self):
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,  
                slow_mo=1000   
            )
            self.context = await self.browser.new_context(
                # Use newer Chrome user agent to avoid "browser not supported" warning
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            self.page = await self.context.new_page()
            print("Browser setup completed successfully")
        except Exception as e:
            print(f"Error in browser setup: {e}")
            await self.cleanup()
            raise e
        
    async def navigate_to_sheet(self):
        await self.page.goto(self.sheet_url)
        
        # Debug: lấy title 
        title = await self.page.title()
        print(f"Page title: {title}")
        
        # Chờ đơn giản hơn
        await self.page.wait_for_timeout(8000)
        
        # Screenshot for debugging
        await self.page.screenshot(path="debug_page_loaded.png")
        print("Page screenshot saved")
        
        # Check for different cell selectors
        selectors_to_check = [
            'div[role="gridcell"]',
            '.cell',
            'td',
            '[data-column]',
            '.docs-sheet-cell',
            '[aria-label*="cell"]'
        ]
        
        for selector in selectors_to_check:
            try:
                elements = await self.page.query_selector_all(selector)
                print(f"Selector '{selector}': found {len(elements)} elements")
                if len(elements) > 0:
                    break
            except Exception as e:
                print(f"Error with selector '{selector}': {e}")
        
        print("Navigation completed")
    
    async def find_and_click_cell(self, cell_reference):
        try:
            await self.page.wait_for_timeout(3000)
            
            # Thử với các selector khác nhau
            cell_selectors_to_try = [
                f'[aria-label*="{cell_reference}"]',
                f'td:nth-child(4)',  # Cột D (index 4)
                'td',  # Generic td elements
                'div[role="gridcell"]'
            ]
            
            print(f"Looking for cell {cell_reference}")
            
            for selector in cell_selectors_to_try:
                try:
                    elements = await self.page.query_selector_all(selector)
                    print(f"Selector '{selector}': found {len(elements)} elements")
                    
                    if len(elements) > 0:
                        if cell_reference == "D2":
                            # Thử TD element đầu tiên cho D2
                            target_index = min(3, len(elements) - 1)  # Cột D
                        elif cell_reference == "D7":
                            # Thử TD element thứ 7 cho D7  
                            target_index = min(7, len(elements) - 1)
                        else:
                            target_index = 0
                        
                        if target_index < len(elements):
                            print(f"Attempting to right-click element at index {target_index}")
                            await elements[target_index].click(button='right')
                            
                            # Chờ context menu hiện
                            await self.page.wait_for_timeout(2000)
                            
                            # Check if context menu appeared
                            menu_items = await self.page.query_selector_all('[role="menuitem"], .goog-menuitem')
                            print(f"Context menu items found: {len(menu_items)}")
                            
                            if len(menu_items) > 0:
                                print(f"Successfully opened context menu for {cell_reference}")
                                return True
                            else:
                                print("No context menu appeared, trying next selector")
                                continue
                                
                except Exception as e:
                    print(f"Error with selector '{selector}': {e}")
                    continue
            
            print(f"Failed to open context menu for {cell_reference}")
            return False
                
        except Exception as e:
            print(f"Error finding cell {cell_reference}: {e}")
            return False
    
    async def capture_edit_history(self, cell_reference):
        if not await self.find_and_click_cell(cell_reference):
            print(f"Failed to find/click cell {cell_reference}")
            return None, None
        
        await self.page.wait_for_timeout(3000)
        
        try:
            # Screenshot context menu for debugging
            await self.page.screenshot(path=f"debug_context_menu_{cell_reference}.png")
            
            # First, try to find edit history in the context menu
            context_history_found = await self.try_context_menu_history()
            
            if not context_history_found:
                print("Edit history not found in context menu, trying main menu...")
                # Try accessing history via main menu
                await self.try_main_menu_history()
            
            await self.page.wait_for_timeout(3000)
            
            # Try to extract history content
            history_content = await self.extract_history_content()
            
            await self.close_edit_history_dialog()
            
            return history_content
            
        except Exception as e:
            print(f"Error in capture_edit_history for {cell_reference}: {e}")
            await self.page.screenshot(path=f"error_{cell_reference}.png")
            return None, None
    
    async def try_context_menu_history(self):
        """Try to find edit history in context menu"""
        edit_history_selectors = [
            'text="Show edit history"',
            'text="View edit history"', 
            'text="Edit history"',
            'text~="history"',  # Fixed syntax
            '[role="menuitem"]:has-text("history")',
            '[role="menuitem"]:has-text("History")',
            '[data-menu-action*="history"]',
            '*:has-text("Show edit history")',
        ]
        
        for i, selector in enumerate(edit_history_selectors):
            try:
                print(f"Trying context menu selector {i+1}: {selector}")
                element = await self.page.wait_for_selector(selector, timeout=1000)
                if element:
                    print(f"Found edit history in context menu with selector: {selector}")
                    await element.click()
                    return True
            except Exception as e:
                continue
        
        return False
    
    async def try_main_menu_history(self):
        """Try to access history via main menu"""
        try:
            # Close context menu first
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(1000)
            
            # Try File menu -> Version history
            file_menu_selectors = [
                'text="File"',
                '[role="menuitem"]:has-text("File")',
                'span:has-text("File")'
            ]
            
            for selector in file_menu_selectors:
                try:
                    file_menu = await self.page.wait_for_selector(selector, timeout=2000)
                    if file_menu:
                        print("Found File menu, clicking...")
                        await file_menu.click()
                        await self.page.wait_for_timeout(1000)
                        
                        # Look for version history
                        version_history_selectors = [
                            'text="Version history"',
                            'text="See version history"',
                            '*:has-text("version history")',
                            '*:has-text("Version history")'
                        ]
                        
                        for vh_selector in version_history_selectors:
                            try:
                                vh_element = await self.page.wait_for_selector(vh_selector, timeout=2000)
                                if vh_element:
                                    print("Found Version history, clicking...")
                                    await vh_element.click()
                                    return True
                            except:
                                continue
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"Error accessing main menu history: {e}")
        
        return False
    
    async def extract_history_content(self):
        try:
            await self.page.wait_for_timeout(3000)
            
            print("Extracting history content...")
            
            # Take screenshot for debugging  
            await self.page.screenshot(path="debug_history_dialog.png")
            
            # Look for version history dialog/panel
            history_dialog_selectors = [
                '[role="dialog"]',
                '.version-history-panel',
                '.docs-version-history',
                '.version-history-container',
                '[data-testid*="history"]',
                '.docs-version-history-panel'
            ]
            
            history_dialog = None
            for selector in history_dialog_selectors:
                try:
                    dialog = await self.page.wait_for_selector(selector, timeout=2000)
                    if dialog:
                        print(f"Found history dialog with selector: {selector}")
                        history_dialog = dialog
                        break
                except:
                    continue
            
            if not history_dialog:
                print("No specific history dialog found, trying to extract from page")
                # If no specific dialog, try to extract version info from page
                return await self.extract_version_info_from_page()
            
            # Extract content from history dialog
            return await self.extract_content_from_dialog(history_dialog)
            
        except Exception as e:
            print(f"Error extracting history content: {e}")
            return "", ""
    
    async def extract_version_info_from_page(self):
        """Extract version information when history panel is open"""
        try:
            # Look for version entries
            version_selectors = [
                '.docs-version-history-item',
                '.version-item',
                '[data-version-id]',
                '.docs-version-history-entry',
                '.history-entry'
            ]
            
            previous_text = ""
            timestamp = ""
            
            for selector in version_selectors:
                try:
                    versions = await self.page.query_selector_all(selector)
                    print(f"Found {len(versions)} versions with selector: {selector}")
                    
                    if len(versions) > 1:  # Need at least 2 versions to get previous
                        # Get the second version (previous edit)
                        prev_version = versions[1]
                        previous_text = await prev_version.inner_text()
                        
                        # Try to extract timestamp from the same element or nearby
                        timestamp_selectors = [
                            '.timestamp',
                            '.date',
                            '.time',
                            '*[title*="ago"]',
                            '*[title*="AM"]',
                            '*[title*="PM"]'
                        ]
                        
                        for ts_selector in timestamp_selectors:
                            try:
                                ts_element = await prev_version.query_selector(ts_selector)
                                if ts_element:
                                    timestamp = await ts_element.inner_text()
                                    break
                            except:
                                continue
                        
                        if previous_text and timestamp:
                            break
                            
                except Exception as e:
                    print(f"Error with version selector {selector}: {e}")
                    continue
            
            if not previous_text:
                print("No version history found, this might be because:")
                print("1. The document has no edit history")
                print("2. The cell hasn't been edited before")
                print("3. Insufficient permissions to view history")
                
                # Return some default indication
                previous_text = "No previous version found"
                timestamp = "N/A"
            
            return previous_text.strip(), timestamp.strip()
            
        except Exception as e:
            print(f"Error extracting version info from page: {e}")
            return "", ""
    
    async def extract_content_from_dialog(self, dialog):
        """Extract content from version history dialog"""
        try:
            dialog_text = await dialog.inner_text()
            print(f"Dialog content length: {len(dialog_text)}")
            
            # For now, return a portion of the dialog content
            lines = dialog_text.split('\n')
            content_lines = [line.strip() for line in lines if line.strip()]
            
            # Look for content that looks like previous edits
            previous_text = ""
            timestamp = ""
            
            for i, line in enumerate(content_lines):
                if any(word in line.lower() for word in ['ago', 'am', 'pm', 'yesterday', 'today']):
                    timestamp = line
                    # The actual content might be nearby
                    if i > 0:
                        previous_text = content_lines[i-1]
                    break
            
            return previous_text.strip(), timestamp.strip()
            
        except Exception as e:
            print(f"Error extracting from dialog: {e}")
            return "", ""
    
    async def close_edit_history_dialog(self):
        try:
            close_selectors = [
                '[aria-label="Close"]',
                '.close-button',
                '[data-action="close"]',
                'button:has-text("Close")',
                '[role="button"]:has-text("×")',
            ]
            
            for selector in close_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        break
                except:
                    continue
            
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(1000)
            
        except Exception as e:
            print(f"Error closing dialog: {e}")
    
    async def capture_all_history(self):
        try:
            await self.setup_browser()
            
            # Kiểm tra xem setup có thành công không
            if not hasattr(self, 'page') or not self.page:
                print("Error: Browser setup failed")
                return
            
            try:
                await self.navigate_to_sheet()
            except Exception as e:
                print(f"Error navigating to sheet: {e}")
                return
            
            try:
                d2_content, d2_timestamp = await self.capture_edit_history("D2")
            except Exception as e:
                print(f"Error capturing D2 history: {e}")
                d2_content, d2_timestamp = None, None
            
            await self.page.wait_for_timeout(3000)
            
            try:
                d7_content, d7_timestamp = await self.capture_edit_history("D7")
            except Exception as e:
                print(f"Error capturing D7 history: {e}")
                d7_content, d7_timestamp = None, None
            
            self.history_data = {
                "content_prev": d2_content or "",
                "timestamp_prev": d2_timestamp or "",
                "requirements_prev": d7_content or "",
                "requirements_timestamp_prev": d7_timestamp or "",
                "capture_date": datetime.now().isoformat()
            }
            
            for key, value in self.history_data.items():
                print(f"{key}: {value}")
            
        except Exception as e:
            await self.page.screenshot(path="error_capture.png")
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        try:
            if hasattr(self, 'page'):
                await self.page.close()
            if hasattr(self, 'context'):
                await self.context.close()
            if hasattr(self, 'browser'):
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def save_history_data(self, filename="data/history.json"):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            return False

async def main():
    sheet_url = "https://docs.google.com/spreadsheets/d/1lNsIW2A1gmurYZ-DJt65xuX_yEsxyvoqPx84Q2B8rEM/edit?gid=0#gid=0"
    
    capture = SheetsEditHistoryCapture(sheet_url)
    
    try:
        await capture.capture_all_history()
        
        success = capture.save_history_data()
        
        if success:
            print("\\n Task completed successfully!")
        else:
            print("\\n Task completed with errors")
            
    except Exception as e:
        print(f"\\n Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())