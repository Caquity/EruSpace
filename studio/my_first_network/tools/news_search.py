"""
News Search Tools
Provides news search and content fetching capabilities using Brave Search API.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Optional

load_dotenv("studio/my_first_network/network_configuration.env")
# logging.basicConfig(level=logging.DEBUG)

def search_hackernews(query: str = "AI", count: int = 2) -> str:
    """
    Search Hacker News using Algolia API.
    
    Args:
        query: Search query (default "AI")
        count: Number of results (default 2)
    
    Returns:
        Formatted search results from Hacker News
    """
    try:
        params = {
            "query": query,
            "hitsPerPage": count,
            "tags": "story"
        }
        response = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params=params,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        hits = data.get("hits", [])
        if not hits:
            return f"No Hacker News results for: {query}"
        
        output = ""
        for i, hit in enumerate(hits, 1):
            title = hit.get("title", "No title")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            points = hit.get("points", 0)
            comments = hit.get("num_comments", 0)
            author = hit.get("author", "unknown")
            
            output += f"{i}. **{title}**\n"
            output += f"   🔗 {url}\n"
            output += f"   ⬆️ {points} points | 💬 {comments} comments | 👤 {author}\n\n"
        
        return output
        
    except Exception as e:
        return f"Hacker News search error: {str(e)}"


def _search_brave(query: str, count: int) -> str:
    """
    Search using Brave Search API.
    
    Args:
        query: Search query string
        count: Number of results to return
    
    Returns:
        Formatted search results
    """
    brave_key = os.getenv("BRAVE_API_KEY")
    if not brave_key:
        return "⚠️ Brave Search API key not configured"
    
    try:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": brave_key
        }
        params = {
            "q": query,
            "count": count,
            "search_lang": "zh-hans",
            "freshness": "pd"  # past day
        }
        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        results = data.get("web", {}).get("results", [])
        if not results:
            return ""
        
        output = ""
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            description = result.get("description", "No description")
            age = result.get("age", "")
            
            output += f"{i}. **{title}**"
            if age:
                output += f" ({age})"
            output += f"\n   🔗 {url}\n"
            if description:
                output += f"   {description}\n"
            output += "\n"
        
        return output
        
    except Exception as e:
        return f"Brave Search error: {str(e)}"


def search_reddit_ai(count: int = 2) -> str:
    """
    Search Reddit for AI-related content.
    
    Args:
        count: Number of results (default 2)
    
    Returns:
        Formatted search results from Reddit AI communities
    """
    queries = [
        "site:reddit.com/r/MachineLearning",
        "site:reddit.com/r/artificial"
    ]
    
    output = ""
    for query in queries:
        result = _search_brave(query, count=1)
        if result and not result.startswith("⚠️"):
            output += result
    
    if not output:
        output = "No Reddit AI news found today.\n\n"
    
    return output


def search_ai_news() -> str:
    """
    Search for AI-related news from Hacker News and Reddit.
    
    Returns:
        Formatted string with AI news (2 from HN, 2 from Reddit)
    """
    output = "🤖 **AI Technology News**\n\n"
    
    # Hacker News (2 items)
    output += "### Hacker News · AI\n\n"
    hn_results = search_hackernews(query="artificial intelligence OR machine learning", count=2)
    output += hn_results + "\n"
    
    # Reddit (2 items total from MachineLearning and artificial)
    output += "### Reddit AI Communities\n\n"
    reddit_results = search_reddit_ai(count=2)
    output += reddit_results + "\n"
    
    return output


def search_travel_news() -> str:
    """
    Search for travel-related news from multiple sources.
    
    Returns:
        Formatted string with travel news (1 Nat Geo, 2 小红书, 2 微博)
    """
    output = "✈️ **Travel & Tourism News**\n\n"
    
    # National Geographic (1 item)
    output += "### National Geographic Travel\n\n"
    natgeo_results = _search_brave(
        "site:nationalgeographic.com travel destinations", 
        count=1
    )
    if natgeo_results and not natgeo_results.startswith("⚠️"):
        output += natgeo_results + "\n"
    else:
        output += "No updates from National Geographic today.\n\n"
    
    # 小红书 (2 items)
    output += "### 小红书 旅游\n\n"
    xhs_results = _search_brave(
        "site:xiaohongshu.com 旅行 攻略", 
        count=2
    )
    if xhs_results and not xhs_results.startswith("⚠️"):
        output += xhs_results + "\n"
    else:
        output += "No updates from 小红书 today.\n\n"
    
    # 微博 (2 items)
    output += "### 新浪微博 旅游\n\n"
    weibo_results = _search_brave(
        "site:weibo.com 旅游 旅行 景点", 
        count=2
    )
    if weibo_results and not weibo_results.startswith("⚠️"):
        output += weibo_results + "\n"
    else:
        output += "No updates from 微博 today.\n\n"
    
    return output


def fetch_webpage(url: str, max_length: int = 8000) -> str:
    """
    Fetch and extract text content from a webpage.
    
    Args:
        url: The URL to fetch
        max_length: Maximum content length to return
    
    Returns:
        Extracted text content
    """
def generate_daily_digest() -> str:
    """
    Generate a combined daily digest of AI and travel news.
    
    Returns:
        Formatted daily digest with 2 HN + 2 Reddit AI news, 
        1 Nat Geo + 2 小红书 + 2 微博 travel news
    """
    from datetime import datetime
    

    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    header = f"""📰 **Daily AI & Travel Brief — {today}**

Welcome to your daily digest of fresh AI technology and travel stories!

---

"""
    
    ai_section = search_ai_news()
    travel_section = search_travel_news()
    
    footer = """
---

📌 Mention @news-assistant anytime to get the latest updates!
"""
    
    return header + ai_section + "\n" + travel_section + footer
    # return f"📄 **{title}**\n🔗 {url}\n\n{text}"
        



def generate_daily_digest(ai_count: int = 3, travel_count: int = 3) -> str:
    """
    Generate a combined daily digest of AI and travel news.
    
    Args:
        ai_count: Number of AI news items per source
        travel_count: Number of travel news items per source
    
    Returns:
        Formatted daily digest
    """
    from datetime import datetime
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    header = f"""📰 **Daily AI & Travel Brief — {today}**

Welcome to your daily digest of fresh AI technology and travel stories!

---

"""
    
    ai_section = search_ai_news(count=ai_count)
    travel_section = search_travel_news(count=travel_count)
    
    footer = """
---

📌 Mention @news-assistant anytime to get the latest updates!
"""
    
    return header + ai_section + "\n" + travel_section + footer


__all__ = ["BraveSearchClient", "search_ai_news", "search_travel_news", "generate_daily_digest"]
