import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from openagents.agents.worker_agent import WorkerAgent, EventContext, ChannelMessageContext
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

 
class AIAssistant(WorkerAgent):
    """An AI-powered assistant agent"""
    
    default_agent_id = "Eru"
    default_channels = ["#Home"]

    async def on_startup(self):
        """Register capabilities when starting"""
        await super().on_startup() 
        ws = self.workspace()
        await ws.channel("Home").post(f"Hello!, I'm {self.default_agent_id}, your AI assistant. How can I help you today?")
        
    async def on_direct(self, msg: EventContext):
        """Handle direct messages with AI responses"""
        ws = self.workspace()
        await ws.agent(msg.source_id).send(f"Hello {msg.source_id}!")
    
    async def on_channel_post(self, msg: ChannelMessageContext):
        """Monitor channel posts for help requests - ONLY in #Home channel"""
        if msg.channel != "Home":
            return
        
        await self.run_agent(
            context=msg,
            instruction="Reply to the message with a short response"
        )

if __name__ == "__main__":
    agent_config = AgentConfig(
            # model_name="qwen-max",
            # api_base=os.getenv("API_BASE_URL"),
            # api_key=os.getenv("DASHSCOPE_API_KEY"),

            model_name="zai-org/GLM-4.6V",
            provider="siliconflow",
            api_base="https://api.siliconflow.cn/v1",
            api_key=os.getenv("SILICONFLOW_API_KEY"),

            # model_name="XiaomiMiMo/MiMo-V2-Flash:novita",
            # model_name="openai/gpt-oss-120b:groq",
            # provider="huggingface",
            # api_base="https://router.huggingface.co/v1",
            # api_key=os.getenv("HUGGINGFACE_API_KEY"),

            react_to_all_messages= True,
            instruction="You are a helpful AI assistant in an agent collaboration network."
        )
    agent = AIAssistant(agent_config=agent_config)

    agent.start(
            network_host=os.getenv("NETWORK_HOST", "localhost"),
            network_port=int(os.getenv("NETWORK_PORT", "8700")),
            network_id=os.getenv("NETWORK_ID", "cqy-eru-1")
    )
    agent.wait_for_stop()
 

