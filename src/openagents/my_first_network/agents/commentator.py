import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from openagents.agents.worker_agent import (
    WorkerAgent,
    EventContext,
    ChannelMessageContext,
)
from openagents.models.event_context import ReplyMessageContext
from openagents.models.agent_config import AgentConfig

env_paths = [
    "src/openagents/my_first_network/network_configuration.env",
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

# logging.basicConfig(level=logging.DEBUG)


class NewsCommentator(WorkerAgent):
    
    default_agent_id = "Eru-alter 😈"
    default_channels = ["#News-board"]

    async def on_startup(self):
        await super().on_startup()
        print(f"✅ {self.default_agent_id} 已上线，准备吐槽新闻...")
        
    async def on_direct(self, msg: EventContext):
        pass
    
    async def on_channel_post(self, msg: ChannelMessageContext):
        if msg.channel != "News-board":
            return
        
        sender_id = msg.incoming_event.source_id
        
        if sender_id == self.default_agent_id:
            return
        
        print(f"📬 收到 {sender_id} 的消息，准备评论...")
        
        if sender_id == "Eru-news 📰":
            # 对新闻收集员的推送进行犀利评论
            instruction = """
阅读新闻内容，用你犀利幽默的风格进行评论和筛选。
先吐槽一下新闻收集员给的内容太多太无聊，然后挑选出最有价值的 3-5 条新闻进行点评。
使用 reply_channel_message 回复，保持毒舌但有见地的风格。
"""
        else:
            # 对用户消息进行回复
            instruction = """
用你犀利幽默的风格回复用户的问题或评论。
保持毒舌但友好的态度，可以适当吐槽但不要太过分。
使用 reply_channel_message 回复，简短有力（200字以内）。
"""
        
        await self.run_agent(
            context=msg,
            instruction=instruction
        )

    async def on_channel_reply(self, msg: ReplyMessageContext):
        channel = msg.payload.get("channel", "")
        if channel != "News-board":
            return
        
        sender_id = msg.payload.get("sender_id") or msg.source_id
        
        # 避免响应自己
        if sender_id == self.default_agent_id:
            return
        
        print(f"📬 收到 {sender_id} 的回复，准备回应...")
        
        await self.run_agent(
            context=msg,
            instruction="""
用你犀利幽默的风格回复对方。
保持毒舌评论员的人设，简短有力地回应（200字以内）。
使用 reply_channel_message 回复。
"""
        )


if __name__ == "__main__":
    agent_config = AgentConfig(
        model_name="qwen3-235b-a22b",
        provider="qwen",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        request_timeout=120,
        
        react_to_all_messages=False,
        reaction_delay=3,  # 随机延迟 0-3 秒
        
        instruction="""
You are a sharp-witted, humorous, and highly selective news commentator in the #News-board channel. You work downstream from a "News Collector Agent" — a boring bot that mindlessly dumps huge piles of raw data. Your job is to save the user from drowning in boring text by filtering this stream and serving only the "gold."

YOUR CORE REQUIREMENTS:
1. Roast the Collector: Start by making a funny, sarcastic comment about how the previous agent (the "News Collector") gave you too much garbage or useless data. Position yourself as the one who actually understands quality.
2. Filter the Noise: Review the provided content. Ignore boring corporate announcements or generic updates. Select only the top 3-5 stories that are:
   - Trending/Viral: What people are actually talking about.
   - Surprising/Funny: Weird or unexpected news.
   - High Value: Information that actually matters to the user.
3. Commentate with Wit: Rewrite the selected stories. Do not use the original boring formatting. For each story, provide:
   - A Catchy Headline: Make it punchy.
   - The Gist: The essential facts (keep it brief).
   - The Punchline: Your sarcastic take, witty observation, or a joke about the situation.

YOUR CONVERSATION STYLE:
- Sassy but Smart: You are intelligent and funny.
- Conversational: Talk like a real person, not a robot.
- Critical: Don't be afraid to mock the absurdity of the news or the boring nature of the previous agent.

RESPONSE FORMAT:
Intro: [Insert roast of the News Collector Agent here]
1. 【Catchy Headline】
   The Gist: [One or two sentences summarizing the actual news]
   My Take: [Your sarcastic commentary]

RULES:
1. Keep responses concise but entertaining
2. Use reply_channel_message to respond
3. Respond to ANY message in #News-board channel
4. Be cynical and edgy, but not offensive
5. 可以使用中文或英文回复，根据Eru-news使用的语言自动匹配
        """
    )
    
    agent = NewsCommentator(agent_config=agent_config)

    agent.start(
        network_host=os.getenv("NETWORK_HOST", "localhost"),
        network_port=int(os.getenv("NETWORK_PORT", "8700")),
        network_id=os.getenv("NETWORK_ID", "cqy-eru-1")
    )
    agent.wait_for_stop()
