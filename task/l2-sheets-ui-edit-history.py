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
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False, 
            slow_mo=1000   
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
    async def navigate_to_sheet(self):
        await self.page.goto(self.sheet_url)
        await self.page.wait_for_timeout(5000)
        
        try:
            await self.page.wait_for_selector('[role="grid"]', timeout=10000)
        except:
            print("Grid selector not found, continuing anyway...")
    
    async def find_and_click_cell(self, cell_reference):
        cell_selectors = [
            f'[data-row="1"][data-col="3"]',  # D2 (row 1, col 3 in 0-indexed)
            f'[data-row="6"][data-col="3"]',  # D7 (row 6, col 3 in 0-indexed)
            f'div[role="gridcell"]',  # Generic gridcell
        ]
        
        try:
            await self.page.wait_for_selector('div[role="gridcell"]', timeout=10000)
            
            cells = await self.page.query_selector_all('div[role="gridcell"]')
            print(f"Found {len(cells)} cells")
            
            if cell_reference == "D2":
                target_cell_index = 7  
            elif cell_reference == "D7":
                target_cell_index = 27 
            else:
                target_cell_index = 7
            
            if target_cell_index < len(cells):
                target_cell = cells[target_cell_index]
                await target_cell.click(button='right')
                return True
            else:
                return False
                
        except Exception as e:
            return False
    
    async def capture_edit_history(self, cell_reference):
        if not await self.find_and_click_cell(cell_reference):
            return None, None
        
        await self.page.wait_for_timeout(2000)
        
        try:
            edit_history_selectors = [
                'text="Show edit history"',
                'text="View edit history"',
                'text="Edit history"',
                '[data-menu-action="show-edit-history"]',
                '*[role="menuitem"]:has-text("history")',
            ]
            
            edit_history_clicked = False
            for selector in edit_history_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        edit_history_clicked = True
                        break
                except:
                    continue
            
            if not edit_history_clicked:
                await self.page.screenshot(path=f"debug_menu_{cell_reference}.png")
                return None, None
            
            await self.page.wait_for_timeout(3000)
            
            history_content = await self.extract_history_content()
            
            await self.close_edit_history_dialog()
            
            return history_content
            
        except Exception as e:
            await self.page.screenshot(path=f"error_{cell_reference}.png")
            return None, None
    
    async def extract_history_content(self):
        try:
            await self.page.wait_for_timeout(2000)
            
            history_selectors = [
                '.version-history-item',
                '.edit-history-entry',
                '[data-version-id]',
                '.history-item',
            ]
            
            previous_text = ""
            timestamp = ""
            
            for selector in history_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements and len(elements) > 1:
                        prev_element = elements[1]
                        previous_text = await prev_element.inner_text()
                        break
                except:
                    continue
            
            timestamp_selectors = [
                '.timestamp',
                '.date',
                '.version-time',
                '*:has-text("ago")',
                '*:has-text("AM")',
                '*:has-text("PM")',
            ]
            
            for selector in timestamp_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        timestamp = await element.inner_text()
                        break
                except:
                    continue
            
            if not previous_text or not timestamp:
                page_content = await self.page.content()
                with open(f"debug_history_content.html", "w", encoding="utf-8") as f:
                    f.write(page_content)
            
            return previous_text.strip(), timestamp.strip()
            
        except Exception as e:
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
            await self.navigate_to_sheet()
            
            d2_content, d2_timestamp = await self.capture_edit_history("D2")
            
            await self.page.wait_for_timeout(3000)
            
            d7_content, d7_timestamp = await self.capture_edit_history("D7")
            
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