"""
Level 2 — Sheets UI "Edit history" - Improved Playwright Implementation
This version includes better error handling and authentication support
"""

import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class ImprovedSheetsCapture:
    def __init__(self, sheet_url):
        self.sheet_url = sheet_url
        self.history_data = {}
        
    async def setup_browser(self):
        """Initialize browser with improved settings"""
        self.playwright = await async_playwright().start()
        
        # Launch browser with better settings for Google Sheets
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            slow_mo=2000,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Create context with user agent
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        self.page = await self.context.new_page()
        
    async def navigate_and_wait(self):
        """Navigate to sheet and wait for it to load properly"""
        print(f"Opening Google Sheets: {self.sheet_url}")
        
        try:
            await self.page.goto(self.sheet_url, wait_until='domcontentloaded')
            print("Page loaded, waiting for sheet to initialize...")
            
            # Wait longer for Google Sheets to fully load
            await self.page.wait_for_timeout(10000)
            
            # Check if we need to sign in
            if "accounts.google.com" in self.page.url:
                print("Google sign-in required. Please sign in manually...")
                # Give user time to sign in manually
                await self.page.wait_for_timeout(30000)
            
            # Wait for sheet-specific elements
            await self.page.wait_for_load_state('networkidle')
            print("Sheet should be ready now")
            
            return True
            
        except Exception as e:
            print(f"Error navigating to sheet: {e}")
            return False
    
    async def try_click_cell_by_coordinates(self, row, col):
        """Try to click a cell using row/column coordinates"""
        try:
            # Google Sheets uses 1-indexed coordinates in the UI
            # D2 = row 2, column 4 (D)
            # D7 = row 7, column 4 (D)
            
            # Try different selector strategies
            selectors_to_try = [
                f'[aria-label*="D{row}"]',
                f'[data-row="{row-1}"][data-col="3"]',  # 0-indexed
                f'.waffle-cell-2,{row-1},3',  # Google Sheets internal class
            ]
            
            for selector in selectors_to_try:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        print(f"Found cell using selector: {selector}")
                        await element.click(button='right')
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error clicking cell D{row}: {e}")
            return False
    
    async def manual_cell_interaction(self, cell_ref):
        """Manual approach - take screenshot and guide user"""
        print(f"\\n=== MANUAL INTERACTION REQUIRED ===")
        print(f"Please manually right-click on cell {cell_ref} and select 'Show edit history'")
        print("Script will wait 30 seconds for you to complete this action...")
        
        # Take screenshot for reference
        await self.page.screenshot(path=f"manual_interaction_{cell_ref}.png")
        print(f"Screenshot saved as: manual_interaction_{cell_ref}.png")
        
        # Wait for user to perform action
        await self.page.wait_for_timeout(30000)
        
        # Try to detect if edit history dialog opened
        history_indicators = [
            'text="Version history"',
            'text="Edit history"', 
            '[aria-label*="history"]',
            '.version-history',
        ]
        
        for indicator in history_indicators:
            try:
                element = await self.page.wait_for_selector(indicator, timeout=2000)
                if element:
                    print("Edit history dialog detected!")
                    return True
            except:
                continue
                
        print("Could not detect edit history dialog. Continuing anyway...")
        return False
    
    async def extract_edit_history_content(self):
        """Extract content from edit history dialog"""
        try:
            # Wait a moment for content to load
            await self.page.wait_for_timeout(3000)
            
            # Take screenshot of current state
            await self.page.screenshot(path="edit_history_dialog.png")
            
            # Try to find previous versions
            content_selectors = [
                '.version-history-item',
                '.edit-history-entry', 
                '[data-version-id]',
                '.history-content',
                '.version-content'
            ]
            
            previous_content = ""
            timestamp = ""
            
            # Try different approaches to extract content
            for selector in content_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements and len(elements) > 1:
                        # Get previous version (second item)
                        prev_element = elements[1]
                        text = await prev_element.inner_text()
                        if text and len(text.strip()) > 0:
                            previous_content = text.strip()
                            break
                except:
                    continue
            
            # Try to find timestamp
            time_selectors = [
                '.timestamp',
                '.time',
                '.date',
                '*:has-text("ago")',
                '*:has-text("AM")',
                '*:has-text("PM")'
            ]
            
            for selector in time_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        time_text = await element.inner_text()
                        if time_text and ("ago" in time_text or "AM" in time_text or "PM" in time_text):
                            timestamp = time_text.strip()
                            break
                except:
                    continue
            
            # If we still don't have content, try getting all visible text
            if not previous_content:
                try:
                    body_text = await self.page.evaluate('document.body.innerText')
                    # Save full content for manual review
                    with open("full_page_content.txt", "w", encoding="utf-8") as f:
                        f.write(body_text)
                    print("Full page content saved to full_page_content.txt for manual review")
                except:
                    pass
            
            return previous_content, timestamp
            
        except Exception as e:
            print(f"Error extracting history content: {e}")
            return "", ""
    
    async def close_dialogs(self):
        """Close any open dialogs"""
        try:
            # Try multiple ways to close
            close_methods = [
                'button[aria-label="Close"]',
                'button:has-text("Close")',
                '[data-action="close"]',
                '.close-button'
            ]
            
            for method in close_methods:
                try:
                    element = await self.page.wait_for_selector(method, timeout=2000)
                    if element:
                        await element.click()
                        break
                except:
                    continue
            
            # Fallback: press Escape
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"Error closing dialogs: {e}")
    
    async def capture_cell_history(self, cell_ref, row_num):
        """Capture edit history for a specific cell"""
        print(f"\\n{'='*50}")
        print(f"CAPTURING EDIT HISTORY FOR {cell_ref}")
        print(f"{'='*50}")
        
        try:
            # Try automated click first
            success = await self.try_click_cell_by_coordinates(row_num, 4)  # Column D = 4
            
            if not success:
                # Fall back to manual interaction
                success = await self.manual_cell_interaction(cell_ref)
            
            if success:
                # Extract content from edit history
                content, timestamp = await self.extract_edit_history_content()
                
                # Close dialogs
                await self.close_dialogs()
                
                return content, timestamp
            else:
                print(f"Failed to access edit history for {cell_ref}")
                return "", ""
                
        except Exception as e:
            print(f"Error capturing {cell_ref} history: {e}")
            return "", ""
    
    async def run_capture(self):
        """Main capture process"""
        try:
            await self.setup_browser()
            
            if not await self.navigate_and_wait():
                print("Failed to navigate to sheet")
                return False
            
            # Capture D2 history
            d2_content, d2_timestamp = await self.capture_cell_history("D2", 2)
            
            # Wait between captures
            await self.page.wait_for_timeout(5000)
            
            # Capture D7 history
            d7_content, d7_timestamp = await self.capture_cell_history("D7", 7)
            
            # Store results
            self.history_data = {
                "content_prev": d2_content,
                "timestamp_prev": d2_timestamp,
                "requirements_prev": d7_content,
                "requirements_timestamp_prev": d7_timestamp,
                "capture_date": datetime.now().isoformat(),
                "method": "playwright_improved"
            }
            
            print(f"\\n{'='*50}")
            print("CAPTURE RESULTS")
            print(f"{'='*50}")
            for key, value in self.history_data.items():
                print(f"{key}: {value}")
            
            return True
            
        except Exception as e:
            print(f"Error in capture process: {e}")
            return False
        
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if hasattr(self, 'browser'):
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def save_results(self, filename="data/history.json"):
        """Save results to JSON file"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            
            print(f"\\nResults saved to: {filename}")
            return True
            
        except Exception as e:
            print(f"Error saving results: {e}")
            return False

async def main():
    """Main execution function"""
    print("Google Sheets Edit History Capture - Improved Version")
    print("This script will attempt to automate right-clicking on D2 and D7")
    print("If automation fails, manual interaction will be required.")
    print("-" * 60)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1lNsIW2A1gmurYZ-DJt65xuX_yEsxyvoqPx84Q2B8rEM/edit?gid=0#gid=0"
    
    capture = ImprovedSheetsCapture(sheet_url)
    
    try:
        success = await capture.run_capture()
        
        if success:
            capture.save_results()
            print("\\n✅ Capture completed!")
        else:
            print("\\n❌ Capture failed")
            
    except KeyboardInterrupt:
        print("\\n⚠️ Capture interrupted by user")
    except Exception as e:
        print(f"\\n❌ Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())