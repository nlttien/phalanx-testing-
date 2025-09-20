import asyncio
import aiohttp
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from dotenv import load_dotenv

load_dotenv()

class BrowserManagerError(Exception):
    pass

class BrowserManager:
    def __init__(self, cdp_port: int = 9222, debug: bool = True):
        self.cdp_port = cdp_port
        self.debug = debug
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # State tracking
        self.is_connected = False
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.screenshot_counter = 0
        
        # Configuration
        self.default_timeout = 30000
        self.default_wait_time = 3000
        
        if self.debug:
            print(f"🎯 BrowserManager initialized (Session: {self.session_id})")
    
    def _log(self, message: str, level: str = "INFO") -> None:
        if self.debug:
            timestamp = datetime.now().strftime("%H:%M:%S")
            prefix = {
                "INFO": "ℹ️",
                "SUCCESS": "✅", 
                "WARNING": "⚠️",
                "ERROR": "❌",
                "DEBUG": "🔍"
            }.get(level, "📝")
            print(f"[{timestamp}] {prefix} {message}")
    
    async def check_cdp_connection(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{self.cdp_port}/json/version",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        browser_info = data.get('Browser', 'Unknown')
                        self._log(f"Found browser via CDP: {browser_info}", "SUCCESS")
                        return True
                    else:
                        self._log(f"CDP responded with status {response.status}", "WARNING")
                        return False
        except asyncio.TimeoutError:
            self._log("CDP connection timeout", "WARNING")
            return False
        except Exception as e:
            self._log(f"CDP connection failed: {e}", "WARNING")
            return False
    
    async def setup_browser(self, new_page: bool = False, headless: bool = False) -> bool:
        try:
            self._log("Setting up browser connection...")
            
            self.playwright = await async_playwright().start()
            
            cdp_available = await self.check_cdp_connection()
            
            if cdp_available:
                # Connect to existing browser via CDP
                self.browser = await self.playwright.chromium.connect_over_cdp(
                    f"http://localhost:{self.cdp_port}"
                )
                self._log("Connected to existing browser via CDP", "SUCCESS")
                
                # Get context and page with error handling
                try:
                    if len(self.browser.contexts) > 0:
                        self.context = self.browser.contexts[0]
                        self._log("Using existing context", "INFO")
                        
                        # Try to use existing page first
                        if len(self.context.pages) > 0 and not new_page:
                            for page in self.context.pages:
                                if page and not page.is_closed():
                                    self.page = page
                                    self._log("Using existing page", "INFO")
                                    break
                        
                        # Create new page if needed
                        if not self.page:
                            self.page = await self.context.new_page()
                            self._log("Created new page in existing context", "INFO")
                    else:
                        self.context = await self.browser.new_context()
                        self.page = await self.context.new_page()
                        self._log("Created new context and page", "INFO")
                        
                except Exception as e:
                    self._log(f"Error with existing browser, creating new context: {e}", "WARNING")
                    self.context = await self.browser.new_context()
                    self.page = await self.context.new_page()
                    self._log("Created new context and page after error", "INFO")
                    
            else:
                # Launch new browser
                self._log("Launching new browser instance...", "INFO")
                self.browser = await self.playwright.chromium.launch(
                    headless=headless,
                    args=['--remote-debugging-port=9222'] if not headless else []
                )
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                self._log("New browser launched successfully", "SUCCESS")
            
            # Verify we have a valid page
            if not self.page:
                raise Exception("Failed to create or obtain a valid page")
            
            # Configure page settings
            try:
                await self.page.set_default_timeout(self.default_timeout)
                self._log("Page configuration completed", "SUCCESS")
            except Exception as e:
                self._log(f"Page configuration failed: {e}", "WARNING")
            
            self.is_connected = True
            self._log("Browser setup completed", "SUCCESS")
            return True
            
        except Exception as e:
            self._log(f"Browser setup failed: {e}", "ERROR")
            self.is_connected = False
            await self._cleanup_on_error()
            raise BrowserManagerError(f"Failed to setup browser: {e}")
    
    async def navigate_to_url(self, url: str, wait_time: Optional[int] = None) -> bool:
        if not self.is_browser_ready():
            raise BrowserManagerError("Browser not ready. Call setup_browser() first.")
        
        try:
            wait_time = wait_time or self.default_wait_time
            self._log(f"Navigating to: {url}")
            
            await self.page.goto(url, timeout=self.default_timeout)
            await self.page.wait_for_timeout(wait_time)
            
            current_url = self.page.url
            if url in current_url or current_url.startswith(url.split('?')[0]):
                self._log(f"Navigation successful to: {current_url}", "SUCCESS")
                return True
            else:
                self._log(f"Navigation redirected to: {current_url}", "WARNING")
                return True
                
        except Exception as e:
            self._log(f"Navigation failed: {e}", "ERROR")
            await self.take_screenshot("navigation_error", f"Failed to navigate to {url}")
            return False
    
    async def take_screenshot(self, name: str = None, description: str = "") -> str:
        if not self.page:
            self._log("Cannot take screenshot - no page available", "ERROR")
            return ""
        
        try:
            self.screenshot_counter += 1
            
            if name is None:
                name = f"screenshot_{self.screenshot_counter:03d}"
            
            screenshots_dir = "screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{self.session_id}_{timestamp}_{name}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            await self.page.screenshot(path=filepath, full_page=True)
            
            log_msg = f"Screenshot saved: {filepath}"
            if description:
                log_msg += f" - {description}"
            self._log(log_msg, "SUCCESS")
            
            return filepath
            
        except Exception as e:
            self._log(f"Screenshot failed: {e}", "ERROR")
            return ""
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        if not self.page:
            return False
            
        try:
            timeout = timeout or self.default_timeout
            await self.page.wait_for_selector(selector, timeout=timeout)
            self._log(f"Element found: {selector}", "SUCCESS")
            return True
        except Exception as e:
            self._log(f"Element not found: {selector} - {e}", "WARNING")
            return False
    
    async def wait_for_any_element(self, selectors: List[str], timeout: Optional[int] = None) -> Optional[str]:
        if not self.page:
            return None
            
        timeout = timeout or self.default_timeout
        
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=1000)
                self._log(f"Element found: {selector}", "SUCCESS")
                return selector
            except:
                continue
        
        self._log(f"None of the elements found: {selectors}", "WARNING")
        return None
    
    async def click_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        try:
            if await self.wait_for_element(selector, timeout):
                await self.page.click(selector)
                self._log(f"Clicked element: {selector}", "SUCCESS")
                return True
            return False
        except Exception as e:
            self._log(f"Click failed on {selector}: {e}", "ERROR")
            return False
    
    async def fill_field(self, selector: str, text: str, timeout: Optional[int] = None) -> bool:
        try:
            if await self.wait_for_element(selector, timeout):
                await self.page.fill(selector, text)
                self._log(f"Filled field {selector} with: {text}", "SUCCESS")
                return True
            return False
        except Exception as e:
            self._log(f"Fill failed on {selector}: {e}", "ERROR")
            return False
    
    def is_browser_ready(self) -> bool:
        return self.is_connected and self.page is not None
    
    def get_page(self) -> Optional[Page]:
        return self.page
    
    def get_browser(self) -> Optional[Browser]:
        return self.browser
    
    def get_context(self) -> Optional[BrowserContext]:
        return self.context
    
    async def _cleanup_on_error(self) -> None:
        try:
            if self.playwright:
                await self.playwright.stop()
        except:
            pass
    
    async def cleanup_browser(self, keep_browser_open: bool = True) -> None:
        try:
            if keep_browser_open:
                self._log("Keeping browser open for session persistence", "INFO")
            else:
                if self.browser:
                    await self.browser.close()
                    self._log("Browser closed", "INFO")
            
            if self.playwright:
                await self.playwright.stop()
                self._log("Playwright stopped", "SUCCESS")
            
            self.is_connected = False
            
        except Exception as e:
            self._log(f"Cleanup error: {e}", "WARNING")


class BrowserContext:
    def __init__(self, cdp_port: int = 9222, new_page: bool = False, 
                 keep_open: bool = True, debug: bool = True):
        self.cdp_port = cdp_port
        self.new_page = new_page
        self.keep_open = keep_open
        self.debug = debug
        self.manager: Optional[BrowserManager] = None
    
    async def __aenter__(self) -> BrowserManager:
        self.manager = BrowserManager(self.cdp_port, self.debug)
        await self.manager.setup_browser(self.new_page)
        return self.manager
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.manager:
            await self.manager.cleanup_browser(self.keep_open)


# Convenience functions
async def get_browser_manager(cdp_port: int = 9222, new_page: bool = False, 
                            debug: bool = True) -> BrowserManager:
    manager = BrowserManager(cdp_port, debug)
    
    if not await manager.check_cdp_connection():
        raise BrowserManagerError(f"No browser found on CDP port {cdp_port}")
    
    await manager.setup_browser(new_page)
    return manager


async def quick_screenshot(url: str, name: str = "quick_screenshot", 
                          cdp_port: int = 9222) -> str:
    async with BrowserContext(cdp_port, new_page=True) as browser:
        await browser.navigate_to_url(url)
        return await browser.take_screenshot(name, f"Quick screenshot of {url}")