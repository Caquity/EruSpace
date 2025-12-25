"""
News Assistant Agent - Mention-driven news assistant with ntfy integration.

This agent:
1. Reads news from ntfy listener's shared storage
2. Responds to mentions (@news-assistant) with latest news
3. Tracks sent messages to avoid duplicates
4. Notifies users when new news arrives

Follows the development pattern from demos/02_tech_news_stream/agents/news_hunter.py
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict

# Add parent directories to path for imports (following news_hunter pattern)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from openagents.agents.worker_agent import WorkerAgent, EventContext, ChannelMessageContext

# Import storage class from ntfy_listener
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))
from ntfy_listener import NtfyNewsStorage


class NewsAssistantAgent(WorkerAgent):
    """
    A news assistant agent that responds to mentions with ntfy news updates.
    
    Features:
    - Reads news from ntfy listener's shared storage
    - Responds only when mentioned
    - Tracks sent news to avoid duplicates
    - Notifies when new news is available
    - Updates approximately every hour
    """

    default_agent_id = "Eru-news"
    default_channels = ["#News-board"]
    
    # Multiple trigger names for mentions
    TRIGGER_NAMES = [
        "@news-assistant",
        "@news_assistant",
        "@Eru-news",
        "@Eru-News",
        "@eru-news",
        "@Eru news",
        "@eru news",
        "@news-assistant",
        "@Eru-news",
        "@eru-news"
    ]

    # Storage file paths (shared with ntfy_listener)
    NEWS_STORAGE_FILE = Path(__file__).parent.parent / "tools" / "latest_news.json"
    SENT_NEWS_FILE = Path(__file__).parent.parent / "tools" / "sent_news.json"

    def __init__(self, check_interval: int = 3600, **kwargs):
        """
        Initialize the news assistant agent.
        
        Args:
            check_interval: Seconds between news checks (default 3600 = 1 hour)
        """
        super().__init__(**kwargs)
        self.check_interval = check_interval
        self.last_sent_news_id = None
        self.last_check_time = None
        self._check_task = None
        self._load_sent_history()
    
    def _load_sent_history(self):
        """load sent news history"""
        try:
            if self.SENT_NEWS_FILE.exists():
                with open(self.SENT_NEWS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.last_sent_news_id = data.get('last_sent_id')
                    self.last_check_time = data.get('last_check_time')
                    print(f"📜 Loaded sent history, last sent: {self.last_sent_news_id}")
        except Exception as e:
            print(f"⚠️  Failed to load history: {e}")
    
    def _save_sent_history(self):
        """save sent news history"""
        try:
            data = {
                'last_sent_id': self.last_sent_news_id,
                'last_check_time': self.last_check_time,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.SENT_NEWS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            ws = self.workspace()
            ws.channel("#News-board").post(
                "🔔 **News Update!**\n\nNew news is available, mention @Eru-news to see the latest content."
            )    
        except Exception as e:
            print(f"⚠️  Failed to save history: {e}")
    
    def is_mentioned(self, text: str) -> bool:
        """
        Check if this agent is mentioned using any of the trigger names.
        
        Overrides the default is_mentioned to support multiple trigger names.
        
        Args:
            text: Message text to check
        
        Returns:
            True if any trigger name is found, False otherwise
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check each trigger name
        for trigger in self.TRIGGER_NAMES:
            # Check both with and without @ symbol
            if trigger.lower() in text_lower:
                print(f"🔔 Trigger detected: '{trigger}' in message")
                return True
        
        return False

    async def on_startup(self):
        """Called when agent starts and connects to the network."""
        print(f"🚀 Eru-News Assistant started!")
        print(f"📡 Listening to news storage: {self.NEWS_STORAGE_FILE}")
        print(f"⏰ Check interval: {self.check_interval} seconds (~{self.check_interval//60} minutes)")
        
        # Announce presence in the News-board channel
        ws = self.workspace()
        await ws.channel("#News-board").post(
            "🗞️ Hi! Eru-News is online! I will offer you the latest news every hour."
        )
        
        # Start the news checking loop
        self._check_task = asyncio.create_task(self._check_news_loop())

    async def on_shutdown(self):
        """Called when agent shuts down."""
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        
        self._save_sent_history()
        print("🛑 Eru-News Assistant stopped.")
    
    async def _check_news_loop(self):
        """Periodically check for news and notify users"""
        # Wait a bit before first check
        await asyncio.sleep(10)
        
        while True:
            try:
                await self._check_for_new_news()
            except Exception as e:
                print(f"❌ Error checking news: {e}")
            
            # Wait for next check cycle
            await asyncio.sleep(self.check_interval)
    
    async def _check_for_new_news(self):
        """Check for new news and notify if available"""
        news = self._load_latest_news()
        
        if not news:
            return
        
        news_id = news.get('id')
        
        # If there is new news and it has not been sent before
        if news_id and news_id != self.last_sent_news_id:
            print(f"📬 Detected new news: {news_id}")
            
            # Send notification to channel
            ws = self.workspace()
            await ws.channel("#News-board").post(
                "🔔 **News Update!**\n\nNew news is available, mention @news-assistant to see the latest content."
            )
            
            # Update check time (but do not update last_sent_news_id, wait for user to view)
            self.last_check_time = datetime.now().isoformat()
            self._save_sent_history()

    def _load_latest_news(self) -> Optional[Dict]:
        """Load latest news from shared storage"""
        try:
            if not self.NEWS_STORAGE_FILE.exists():
                return None
            
            with open(self.NEWS_STORAGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load news: {e}")
            return None
    
    def _parse_news(self, news_data: Dict) -> str:
        """
        Parse news data and format output - minimal and clean
        
        Format:
        📰 Title Here
        🏷️ Source | 📅 Time
        🔗 URL
        
        """
        try:
            message = news_data.get('message', '(No content)')
            topic = news_data.get('topic', 'Unknown')
            url = news_data.get('url', '')
            time_str = news_data.get('received_time', '')
            news_id = news_data.get('id', 'N/A')
            
            # Try to parse message as JSON (if structured data)
            try:
                msg_obj = json.loads(message)
                title = msg_obj.get('title', message)
                url = msg_obj.get('url', url)
                source = msg_obj.get('source', topic)
            except:
                # If not JSON, use raw message
                title = message
                source = topic.split('-')[0] if '-' in topic else topic
            
            # Format time
            if time_str:
                try:
                    dt = datetime.fromisoformat(time_str)
                    time_display = dt.strftime('%m-%d %H:%M')
                except:
                    time_display = time_str[:16] if len(time_str) > 16 else time_str
            else:
                time_display = "Unknown"
            
            # Build minimal clean output
            output = f"📰 {title}\n"
            output += f"🏷️ {source} | 📅 {time_display}\n"
            if url:
                output += f"🔗 {url}"
            
            return output
            
        except Exception as e:
            print(f"❌ Failed to parse news: {e}")
            return f"Failed to parse news content: {str(e)}"
    
    async def on_direct(self, msg: EventContext):
        """
        Handle direct messages - send latest news.
        
        Args:
            msg: Direct message event context
        """
        try:
            sender_id = msg.incoming_event.source_id
            print(f"📬 Received direct message from {sender_id}")
            
            # Get and send news
            news_message = await self._get_latest_news_message()
            
            ws = self.workspace()
            await ws.agent(sender_id).send(news_message)
            print(f"📤 Sent news to {sender_id}")
            
        except Exception as e:
            print(f"❌ Error handling direct message: {e}")
            import traceback
            traceback.print_exc()

    async def on_channel_mention(self, msg: ChannelMessageContext):
        """
        Handle mentions of @news-assistant in channels.
        
        This method is called by WorkerAgent when the agent is mentioned.
        
        Args:
            msg: Channel message event context
        """
        try:
            sender_id = msg.incoming_event.source_id
            payload = msg.incoming_event.payload
            
            channel = "#News-board"
            if isinstance(payload, dict):
                channel = payload.get('channel', '#News-board')
            
            if hasattr(msg, 'channel'):
                channel = msg.channel
            
            print(f"🔔 {sender_id} mentioned me in {channel}")
            
            # Avoid responding to self
            if sender_id == self.default_agent_id:
                return
            
            # Get and send news
            news_message = await self._get_latest_news_message()
            
            ws = self.workspace()
            await ws.channel(channel).post_with_mention(
                news_message,
                mention_agent_id=sender_id
            )
            print(f"✅ Sent news to {sender_id} in {channel}")
            
        except Exception as e:
            print(f"❌ Error handling mention: {e}")
            import traceback
            traceback.print_exc()
    
    async def on_channel_post(self, msg: ChannelMessageContext):
        """
        Monitor channel posts (without mentions).
        
        This is called for messages that don't mention the agent.
        We can ignore these or add custom logic here.
        
        Args:
            msg: Channel message event context
        """
        # Not used for this agent - we only respond to mentions
        pass

    async def _get_latest_news_message(self) -> str:
        """
        Get the latest news message, checking for updates.
        
        Returns:
            Formatted news message string
        """
        news = await asyncio.to_thread(self._load_latest_news)
        
        # Check if storage is empty
        if not news:
            # Check if there's a sent marker
            sent_marker = await asyncio.to_thread(NtfyNewsStorage.get_sent_marker)
            
            if sent_marker:
                # News was recently sent and cleared
                sent_time_str = sent_marker.get('sent_at', '')
                try:
                    sent_time = datetime.fromisoformat(sent_time_str)
                    time_ago = datetime.now() - sent_time
                    minutes_ago = int(time_ago.total_seconds() / 60)
                    
                    if minutes_ago < 60:
                        msg = "\n📰 News is already sent\n\n"
                        msg += f"✅ The latest news was successfully sent {minutes_ago} minutes ago\n"
                        msg += "⏰ Please try again later, new content will be updated automatically when received\n"
                        return msg
                except:
                    pass
            
            # No marker, listener might not be running
            msg = "\n📭 No news available\n\n"
            msg += "⚠️ Currently no news content is available\n\n"
            msg += "Please ensure the ntfy listener is running:\n"
            msg += "  python src/openagents/my_first_network/tools/ntfy_listener.py\n"
            return msg
        
        news_id = news.get('id')
        
        # Check if the news has already been sent
        if news_id == self.last_sent_news_id:
            # Check last check time
            if self.last_check_time:
                try:
                    last_check = datetime.fromisoformat(self.last_check_time)
                    time_diff = datetime.now() - last_check
                    
                    if time_diff < timedelta(hours=1):
                        minutes_left = int((timedelta(hours=1) - time_diff).total_seconds() / 60)
                        
                        msg = "\n📰 News status\n\n"
                        msg += f"⏰ Updates in approximately {minutes_left} minutes\n"
                        return msg
                except:
                    pass
        
        # Mark as sent and clear storage
        self.last_sent_news_id = news_id
        self.last_check_time = datetime.now().isoformat()
        self._save_sent_history()
        
        # Clear storage after successful send
        await asyncio.to_thread(NtfyNewsStorage.mark_as_sent, news_id)
        
        # Format and return news with minimal layout
        header = "\n📰 Eru-news\n" + "═" * 68 + "\n\n"
        
        news_content = self._parse_news(news)
        
        footer = "\n\n⏰ Updates approximately every hour."
        
        return header + news_content + footer


async def main():
    """Run the news assistant agent."""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    
    env_paths = [
        Path(__file__).parent.parent / "network_configuration.env",
        "network_configuration.env",
        ".env"
    ]
    for env_path in env_paths:
        if Path(env_path).exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from {env_path}")
            break
    else:
        print("ℹ️  No .env file found, using system environment variables")
    
    # Use environment variables with Docker-friendly defaults
    network_host = os.getenv("NETWORK_HOST", "localhost")
    network_port = int(os.getenv("NETWORK_PORT", "8700"))
    network_id = os.getenv("NETWORK_ID", "cqy-eru-1")
    
    print(f"🚀 Starting Eru-News Assistant...")
    print(f"   Network: {network_host}:{network_port}")
    print(f"   Network ID: {network_id}")

    agent = NewsAssistantAgent(check_interval=3600)  # Check every hour

    try:
        await agent.async_start(
            network_host=network_host,
            network_port=network_port,
            network_id=network_id,
        )

        # Keep running until interrupted
        print(f"\n✅ Eru-News Assistant running.")
        print(f"   Mention @news-assistant to get latest news.")
        print(f"   Press Ctrl+C to stop.\n")
        
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down Eru-News Assistant...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await agent.async_stop()
        print("👋 Eru-News Assistant stopped.")


if __name__ == "__main__":
    asyncio.run(main())
