import time
import logging
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from base_watcher import BaseWatcher


class InstagramWatcher(BaseWatcher):
    def __init__(self, vault_path: str = 'AI_Employee_Vault', session_path: str = 'instagram_session', interval: int = 120):
        super().__init__(vault_path=vault_path, check_interval=interval)
        self.session_path = Path(session_path)
        self.platform = 'instagram'
        self.keywords = ['sales', 'client', 'opportunity']
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_for_updates(self) -> list:
        """Launch persistent browser headless, check Instagram feed/notifications for unread mentions."""
        updates = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=True
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            try:
                # Navigate to Instagram notifications
                page.goto('https://www.instagram.com/accounts/activity/', wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(5000)
                
                # Find notification items
                notifications = page.query_selector_all('article, div[role="button"][tabindex="0"]')
                
                for notification in notifications:
                    try:
                        text = notification.inner_text().lower()
                        
                        # Check if contains keywords
                        if any(keyword in text for keyword in self.keywords):
                            # Check if unread (look for blue dot or unread indicators)
                            unread_indicator = notification.query_selector('[class*="unread"]') or \
                                              notification.query_selector('svg[class*="dot"]') or \
                                              notification.query_selector('[aria-label*="unread"]')
                            
                            is_unread = unread_indicator is not None
                            
                            updates.append({
                                'platform': self.platform,
                                'content': notification.inner_text().strip(),
                                'timestamp': datetime.now().isoformat(),
                                'keywords_found': [k for k in self.keywords if k in text],
                                'is_unread': is_unread
                            })
                    except Exception as e:
                        self.logger.debug(f"Error processing notification: {e}")
                        continue
                
                # Also check direct messages for keywords
                page.goto('https://www.instagram.com/direct/inbox/', wait_until='networkidle', timeout=30000)
                page.wait_for_timeout(3000)
                
                messages = page.query_selector_all('div[role="button"][tabindex="0"]')
                
                for message in messages:
                    try:
                        text = message.inner_text().lower()
                        
                        if any(keyword in text for keyword in self.keywords):
                            updates.append({
                                'platform': self.platform,
                                'content': f"DM: {message.inner_text().strip()}",
                                'timestamp': datetime.now().isoformat(),
                                'keywords_found': [k for k in self.keywords if k in text],
                                'is_unread': True
                            })
                    except Exception as e:
                        self.logger.debug(f"Error processing message: {e}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error checking Instagram: {e}")
            finally:
                browser.close()
        
        return updates

    def create_action_file(self, item: dict) -> Path:
        """Create action file in Needs_Action with frontmatter and suggested actions."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"INSTAGRAM_{timestamp}.md"
        action_file = self.needs_action / filename
        
        # Generate suggested actions based on keywords
        suggested_actions = []
        if 'sales' in item.get('keywords_found', []):
            suggested_actions.append('- Review sales inquiry from Instagram')
            suggested_actions.append('- Check if lead qualifies for follow-up')
        if 'client' in item.get('keywords_found', []):
            suggested_actions.append('- Verify client identity and account')
            suggested_actions.append('- Respond to client inquiry professionally')
        if 'opportunity' in item.get('keywords_found', []):
            suggested_actions.append('- Assess opportunity potential')
            suggested_actions.append('- Move conversation to appropriate channel if needed')
        
        if not suggested_actions:
            suggested_actions = ['- Review Instagram notification and determine appropriate action']
        
        content = f"""---
type: {item['platform']}
content: |
  {item['content']}
priority: medium
timestamp: {item['timestamp']}
keywords: {', '.join(item.get('keywords_found', []))}
is_unread: {str(item.get('is_unread', False)).lower()}
---

# Instagram Notification Action Required

## Content
{item['content']}

## Suggested Actions
{chr(10).join(suggested_actions)}

## Notes
- Review the notification on Instagram for full context
- Respond appropriately based on business priorities
- Update this file with actions taken in the Notes section below

---
*Generated by InstagramWatcher*
"""
        
        action_file.write_text(content, encoding='utf-8')
        self.logger.info(f"Created action file: {action_file}")
        
        return action_file


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    watcher = InstagramWatcher()
    watcher.run()
