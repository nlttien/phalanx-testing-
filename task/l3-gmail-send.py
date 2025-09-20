import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from browser_manager import BrowserManager

load_dotenv()

class GmailAutoSender:
    def __init__(self, cdp_port=9222):
        self.browser_manager = BrowserManager(cdp_port, debug=True)
        
        self.recipient_contact_data = None
        self.email_content_data = None
        self.sent_proof_path = None
    
    @property
    def page(self):
        return self.browser_manager.get_page()
    
    @property 
    def browser(self):
        return self.browser_manager.get_browser()
    
    @property
    def context(self):
        return self.browser_manager.get_context()
    
    def load_recipient_contact_data(self, file_path=None):
        try:
            if file_path is None:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(os.path.dirname(current_dir), "data", "basic_row.json")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                self.recipient_contact_data = json.load(f)
                return True
        except Exception as e:
            return False
    
    def load_history_content_data(self, file_path=None):
        try:
            if file_path is None:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                data_dir = os.path.join(os.path.dirname(current_dir), "data")
                file_path = os.path.join(data_dir, "history.json")
            
            if not os.path.exists(file_path):
                current_dir = os.path.dirname(os.path.abspath(__file__))
                data_dir = os.path.join(os.path.dirname(current_dir), "data")
                file_path = os.path.join(data_dir, "history_mock.json")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                self.email_content_data = json.load(f)
                return True
        except Exception as e:
            return False
    
    async def navigate_to_gmail(self):
        try:
            gmail_url = os.getenv('GMAIL_URL', 'https://mail.google.com')
            
            await self.browser_manager.navigate_to_url(gmail_url, 8000)
            
            await self.browser_manager.take_screenshot("debug_gmail_loaded.png", "Gmail loaded")
            
            compose_selectors = [
                '[data-tooltip="Compose"]',
                '[aria-label="Compose"]',
                '[role="button"]:has-text("Compose")',
                '.T-I.T-I-KE.L3',  # Gmail's compose button class
                '[data-tooltip="Soạn"]',  # Vietnamese
                '[aria-label="Soạn"]',
                'div[role="button"]:has-text("Compose")',
                'button:has-text("Compose")'
            ]
            
            compose_found = False
            for i, selector in enumerate(compose_selectors):
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    compose_found = True
                    break
                except:
                    continue
            
            if compose_found:
                return True
            
            await self.page.screenshot(path="debug_gmail_no_compose.png")
            
        except Exception as e:
            await self.page.screenshot(path="debug_gmail_navigation_error.png")
            return False
    
    async def open_compose_window(self):
        try:
            compose_selectors = [
                '[data-tooltip="Compose"]',
                '[aria-label="Compose"]',
                '[role="button"]:has-text("Compose")',
                '.T-I.T-I-KE.L3'  # Gmail's compose button class
            ]
            
            compose_button = None
            for selector in compose_selectors:
                try:
                    compose_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if compose_button:
                        print(f"Found compose button with selector: {selector}")
                        break
                except:
                    continue
            
            if not compose_button:
                await self.page.screenshot(path="debug_no_compose_button.png")
                return False
            
            await compose_button.click()
            await self.page.wait_for_timeout(2000)
            
            compose_window_selectors = [
                '[role="dialog"]',
                '.nH .Hq',  # Gmail compose dialog
                '.nH.aqJ',
                '.aYF'      # Another compose window class
            ]
            
            compose_window = None
            for selector in compose_window_selectors:
                try:
                    compose_window = await self.page.wait_for_selector(selector, timeout=5000)
                    if compose_window:
                        break
                except:
                    continue
            
            if not compose_window:
                await self.page.screenshot(path="debug_no_compose_window.png")
                return False
            
            await self.page.screenshot(path="debug_compose_window_opened.png")
            return True
            
        except Exception as e:
            await self.page.screenshot(path="debug_compose_error.png")
            return False
    
    async def fill_contenteditable_field(self, element, text):
        try:
            await element.click()
            await self.page.wait_for_timeout(500)
            
            await self.page.keyboard.press('Control+a')
            await self.page.wait_for_timeout(200)
            
            await self.page.keyboard.type(text)
            await self.page.wait_for_timeout(500)
            
            return True
        except Exception as e:
            print(f"Error filling contenteditable field: {e}")
            return False
    
    async def fill_email_fields(self):
        try:
            if not self.recipient_contact_data or not self.email_content_data:
                return False
            
            to_email = self.recipient_contact_data.get('Email', '')
            if to_email:
                to_selectors = [
                    # Most common Gmail selectors
                    '[name="to"] [contenteditable="true"]',
                    '[aria-label="To recipients"] [contenteditable="true"]',
                    'div[aria-label="To recipients"] [contenteditable="true"]',
                    '[role="combobox"][aria-label*="To"]',
                    
                    # Fallback selectors
                    'input[name="to"]',
                    'textarea[name="to"]',
                    '[aria-label="To"]',
                    '.oL.aDm [contenteditable="true"]',
                    '[role="textbox"][aria-label*="To"]',
                    '[data-hovercard-id*="to"]',
                    
                    # Generic contenteditable in compose area
                    '.nH [contenteditable="true"]',
                    '.aYF [contenteditable="true"]'
                ]
                
                to_field = None
                used_selector = None
                for i, selector in enumerate(to_selectors):
                    try:
                        to_field = await self.page.wait_for_selector(selector, timeout=2000)
                        if to_field:
                            print(f"Found To field with selector {i+1}: {selector}")
                            break
                    except:
                        continue
                
                if to_field:
                    try:
                        await to_field.fill(to_email)
                        await self.page.wait_for_timeout(1000)
                        
                        value = await to_field.input_value() if hasattr(to_field, 'input_value') else ""
                        if to_email in value:
                            print(f"✅ Filled To field (method 1 - fill): {to_email}")
                    except Exception as e:
                        print(f"Method 1 failed: {e}")
                else:
                    await self.page.screenshot(path="debug_no_to_field.png")
                    return False
            
            subject = self.recipient_contact_data.get('Subject', '')
            if subject:
                subject_selectors = [
                    'input[name="subjectbox"]',
                    'input[aria-label="Subject"]',
                    '[placeholder*="Subject"]',
                    '[aria-label="Subject"] input',
                    '.aoT input',  # Gmail subject field class
                    '[role="textbox"][aria-label*="Subject"]'
                ]
                
                subject_field = None
                for selector in subject_selectors:
                    try:
                        subject_field = await self.page.wait_for_selector(selector, timeout=3000)
                        if subject_field:
                            print(f"Found Subject field with selector: {selector}")
                            break
                    except:
                        continue
                
                if subject_field:
                    try:
                        await subject_field.fill(subject)
                        await self.page.wait_for_timeout(1000)
                    except:
                        if await self.fill_contenteditable_field(subject_field, subject):
                            print(f"Filled Subject field (contenteditable): {subject}")
                        else:
                            print("Could not fill Subject field")
                            return False
                else:
                    print("Could not find Subject field")
                    return False
            
            # Fill Body field
            user_name = self.recipient_contact_data.get('User Name', 'User')
            content_prev = self.email_content_data.get('content_prev', '')
            requirements_prev = self.email_content_data.get('requirements_prev', '')
            
            email_body = f"""Dear {user_name},
            
            {content_prev}

            {requirements_prev}"""
            
            body_selectors = [
                '[role="textbox"][aria-label*="Message"]',
                '[contenteditable="true"][role="textbox"]',
                '.Am.Al.editable',  # Gmail body editor
                '[aria-label*="Message body"] [contenteditable="true"]',
                '.ii.gt .a3s',
                'div[contenteditable="true"][role="textbox"]'
            ]
            
            body_field = None
            for selector in body_selectors:
                try:
                    body_field = await self.page.wait_for_selector(selector, timeout=3000)
                    if body_field:
                        print(f"Found Body field with selector: {selector}")
                        break
                except:
                    continue
            
            if body_field:
                if await self.fill_contenteditable_field(body_field, email_body):
                    print(f"Filled Body field")
                else:
                    print("Could not fill Body field")
                    return False
            else:
                print("Could not find Body field")
                return False
            
            await self.page.screenshot(path="debug_email_filled.png")
            
            try:
                to_verification_selectors = [
                    '[aria-label*="To"] [data-hovercard-id]',  # Gmail recipient chips
                    '.vR span[email]',  # Recipient spans
                    '[role="option"]',  # Autocomplete options
                    '.vR .go span'  # Another recipient indicator
                ]
                
                to_verified = False
                for selector in to_verification_selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if len(elements) > 0:
                            print(f"To field verification passed: found {len(elements)} recipient(s)")
                            to_verified = True
                            break
                    except:
                        continue
                
                if not to_verified:
                    print("Could not verify To field content, but proceeding...")
            except Exception as e:
                print(f"Verification error: {e}")

            return True
            
        except Exception as e:
            print(f"Error filling email fields: {e}")
            await self.page.screenshot(path="debug_fill_fields_error.png")
            return False
    
    async def send_email(self):
        try:
            send_selectors = [
                '[role="button"][aria-label*="Send"]',
                '[data-tooltip="Send"]',
                '.T-I.J-J5-Ji.aoO.v7.T-I-atl.L3', 
                '[role="button"]:has-text("Send")'
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if send_button:
                        print(f"Found Send button with selector: {selector}")
                        break
                except:
                    continue
            
            if not send_button:
                await self.page.screenshot(path="debug_no_send_button.png")
                return False
            
            await self.page.screenshot(path="debug_before_send.png")
            
            await send_button.click()
            
            await self.page.wait_for_timeout(5000)
            
            sent_indicators = [
                '[role="alert"]:has-text("sent")',
                '.aOy:has-text("sent")',
                '.b7.J-M',  # Gmail sent notification
                ':has-text("Message sent")',
                ':has-text("Your message has been sent")',
                '[data-tooltip*="sent"]',
                '.kv:has-text("sent")'  # Gmail status indicator
            ]
            
            sent_confirmed = False
            for selector in sent_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        sent_confirmed = True
                        break
                except:
                    continue
            
            if not sent_confirmed:
                try:
                    inbox_indicators = [
                        '[aria-label="Inbox"]',
                        '.TO.zE',  # Gmail inbox
                        ':has-text("Inbox")',
                        '.nZ:has-text("Inbox")'
                    ]
                    
                    for selector in inbox_indicators:
                        try:
                            element = await self.page.wait_for_selector(selector, timeout=3000)
                            if element:
                                sent_confirmed = True
                                break
                        except:
                            continue
                except:
                    pass
            
            navigated_to_sent = False
            try:
                sent_folder_selectors = [
                    '[href*="sent"]',
                    '[title="Sent"]',
                    '.TK .nZ:has-text("Sent")',
                    '[aria-label="Sent"]'
                ]
                
                for selector in sent_folder_selectors:
                    try:
                        sent_folder = await self.page.wait_for_selector(selector, timeout=3000)
                        if sent_folder:
                            await sent_folder.click()
                            await self.page.wait_for_timeout(3000)
                            navigated_to_sent = True
                            break
                    except:
                        continue
            except:
                print("Could not navigate to Sent folder")
            
            if navigated_to_sent and not sent_confirmed:
                print("Email likely sent successfully (navigated to Sent folder)")
                sent_confirmed = True
            
            # Capture final proof screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(current_dir), "data")
            self.sent_proof_path = os.path.join(data_dir, f"../data/sent_proof_{timestamp}.png")
            
            os.makedirs(data_dir, exist_ok=True)
            await self.page.screenshot(path=self.sent_proof_path)

            print(f"Proof screenshot saved: {self.sent_proof_path}")

            return sent_confirmed
            
        except Exception as e:
            print(f"Error sending email: {e}")
            await self.page.screenshot(path="debug_send_error.png")
            return False
    
    async def send_email_workflow(self):
        try:
            # Load data from previous levels
            if not self.load_recipient_contact_data():
                return False
            
            if not self.load_history_content_data():
                return False
            
            # Setup browser
            await self.browser_manager.setup_browser()
            
            # Navigate to Gmail
            if not await self.browser_manager.navigate_to_url("https://mail.google.com", 8000):
                return False
            
            # Open compose window
            if not await self.open_compose_window():
                return False
            
            # Fill email fields
            if not await self.fill_email_fields():
                return False
            
            # Send email
            if not await self.send_email():
                return False
            
            print("✅ Email sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error in email workflow: {e}")
            return False
        
        finally:
            await self.cleanup_browser()
    
    async def cleanup_browser(self):
        """Clean up browser resources using browser manager"""
        await self.browser_manager.cleanup_browser(keep_browser_open=True)
    
    def save_send_report(self, success=True):
        """Save sending report with proof"""
        try:
            report = {
                "level3_execution": {
                    "timestamp": datetime.now().isoformat(),
                    "success": success,
                    "recipient": self.recipient_contact_data.get('Email', '') if self.recipient_contact_data else '',
                    "subject": self.recipient_contact_data.get('Subject', '') if self.recipient_contact_data else '',
                    "proof_screenshot": self.sent_proof_path,
                    "level1_data_used": self.recipient_contact_data,
                    "level2_data_used": self.email_content_data
                }
            }
            
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(current_dir), "data")
            report_path = os.path.join(data_dir, "level3_send_report.json")
            
            os.makedirs(data_dir, exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"Send report saved: {report_path}")
            
        except Exception as e:
            print(f"Error saving send report: {e}")

async def main():
    sender = GmailAutoSender()

    cdp_available = await sender.browser_manager.check_cdp_connection()
    if not cdp_available:
        print("No browser found via CDP. Please start Chrome with CDP enabled.")
        print("Run: start-chrome-cdp-simple.bat")
        return
    
    try:
        success = await sender.send_email_workflow()
        sender.save_send_report(success)
        
        if success:
            print(f"Email sent with proof saved to: {sender.sent_proof_path}")
        else:
            print("\nLevel 3 completed with errors")

    except KeyboardInterrupt:
        if hasattr(sender, 'cleanup_browser'):
            await sender.cleanup_browser()
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if hasattr(sender, 'cleanup_browser'):
            await sender.cleanup_browser()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript interrupted")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        print("👋 Goodbye!")