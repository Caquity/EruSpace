"""
Ntfy News Listener - Listen to ntfy push notifications and store news
"""

import requests
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional


class NtfyNewsStorage:
    """Share storage for ntfy news messages"""
    
    STORAGE_FILE = Path(__file__).parent / "latest_news.json"
    SENT_MARKER_FILE = Path(__file__).parent / "news_sent_marker.json"
    
    @classmethod
    def save_news(cls, news_data: dict):
        """
        Save news to file
        
        Args:
            news_data: Dictionary containing news content
        """
        try:
            with open(cls.STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(news_data, f, ensure_ascii=False, indent=2)
            print(f"💾 News saved: {news_data.get('message', '')[:50]}...")
        except Exception as e:
            print(f"❌ Save failed: {e}")
    
    @classmethod
    def load_news(cls) -> Optional[dict]:
        """
        Load latest news from file
        
        Returns:
            News data dictionary, or None if not available
        """
        try:
            if not cls.STORAGE_FILE.exists():
                return None
            
            with open(cls.STORAGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Load failed: {e}")
            return None
    
    @classmethod
    def clear_news(cls):
        """Clear news storage"""
        try:
            if cls.STORAGE_FILE.exists():
                cls.STORAGE_FILE.unlink()
        except Exception as e:
            print(f"❌ Clear failed: {e}")
    
    @classmethod
    def mark_as_sent(cls, news_id: str):
        """Mark news as successfully sent and clear storage"""
        try:
            # Record sent marker
            marker_data = {
                'last_sent_id': news_id,
                'sent_at': datetime.now().isoformat(),
                'status': 'delivered'
            }
            with open(cls.SENT_MARKER_FILE, 'w', encoding='utf-8') as f:
                json.dump(marker_data, f, ensure_ascii=False, indent=2)
            
            # Clear news storage
            if cls.STORAGE_FILE.exists():
                cls.STORAGE_FILE.unlink()
            
            print(f"✅ News {news_id} marked as sent and storage cleared")
        except Exception as e:
            print(f"❌ Mark as sent failed: {e}")
    
    @classmethod
    def get_sent_marker(cls) -> Optional[dict]:
        """Get the sent marker information"""
        try:
            if not cls.SENT_MARKER_FILE.exists():
                return None
            
            with open(cls.SENT_MARKER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Load sent marker failed: {e}")
            return None


class NtfyNewsListener:
    """Listen to ntfy push notifications and store news"""
    
    def __init__(self, topic: str):
        """
        Initialize listener
        
        Args:
            topic: ntfy topic name
        """
        self.topic = topic
        self.url = f"https://ntfy.sh/{topic}"
        self.message_count = 0
        self.latest_message_id = None
    
    def parse_message(self, line: bytes) -> Optional[dict]:
        """Parse message"""
        try:
            text = line.decode('utf-8')
            return json.loads(text)
        except Exception as e:
            print(f"⚠️  Parse failed: {e}")
            return None
    
    def format_time(self, timestamp: int) -> str:
        """Format timestamp"""
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    def handle_message(self, line: bytes):
        """Handle single message"""
        if not line:
            return
        
        data = self.parse_message(line)
        if not data:
            return
        
        event_type = data.get('event', 'unknown')
        
        if event_type == 'open':
            print("\n╔" + "═" * 68 + "╗")
            print("║ 🔗 Connection established" + " " * 38 + "║")
            print("╠" + "═" * 68 + "╣")
            print(f"║ Topic: {data.get('topic', 'N/A'):<59} ║")
            print(f"║ Time: {self.format_time(data.get('time', 0)):<59}  ║")
            print("╚" + "═" * 68 + "╝\n")
        
        elif event_type == 'keepalive':
            print(f"🔗 ONLINE [{self.format_time(data.get('time', 0))}]", end='\r', flush=True)
        
        elif event_type == 'message':
            self.message_count += 1
            message_id = data.get('id', 'N/A')
            
            # Check if new message
            if message_id != self.latest_message_id:
                self.latest_message_id = message_id
                
                # add received time and message number
                data['received_time'] = datetime.now().isoformat()
                data['message_number'] = self.message_count
                
                # Save to storage
                NtfyNewsStorage.save_news(data)
                
                # Display message
                print("\n╔" + "═" * 68 + "╗")
                print(f"║ 📬 New message #{self.message_count:<54} ║")
                print("╠" + "═" * 68 + "╣")
                print(f"║ Topic: {data.get('topic', 'N/A'):<59} ║")
                print(f"║ Time: {self.format_time(data.get('time', 0)):<59} ║")
                print(f"║ ID:   {message_id:<59} ║")
                print("╠" + "═" * 68 + "╣")
                
                message = data.get('message', '(No content)')
                lines = message.split('\n')
                print("║ Content:" + " " * 62 + "║")
                for line in lines:
                    if len(line) > 65:
                        line = line[:62] + "..."
                    print(f"║   {line:<65} ║")
                
                print("╚" + "═" * 68 + "╝\n")
                print(f"✅ Saved to shared storage, waiting for Agent to read")
    
    def listen(self):
        """Listen to message stream"""
        print(f"🚀 Ntfy News Listener started")
        print(f"📡 Topic: {self.topic}")
        print(f"📡 URL: {self.url}")
        print(f"💾 Storage location: {NtfyNewsStorage.STORAGE_FILE}")
        print("=" * 70)
        
        try:
            resp = requests.get(self.url, stream=True)
            
            for line in resp.iter_lines():
                self.handle_message(line)
        
        except KeyboardInterrupt:
            print("\n\n" + "=" * 70)
            print(f"👋 Stopped listening, received {self.message_count} messages in total")
            print("=" * 70)
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    listener = NtfyNewsListener("trendradar-Caquity-createdOn13Dec2025/json")
    listener.listen()
