import asyncio
import os
import logging
from dotenv import load_dotenv
from openagents.agents.worker_agent import WorkerAgent, EventContext, ChannelMessageContext
from openagents.models.agent_config import AgentConfig

load_dotenv("studio/my_first_network/network_configuration.env")
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
        """Monitor channel posts for help requests"""
        await self.run_agent(
            context=msg,
            instruction="Reply to the message with a short response"
        )

if __name__ == "__main__":
    agent_config = AgentConfig(
            # model_name="qwen3-max",
            # api_base=os.getenv("API_BASE_URL"),
            # api_key=os.getenv("DASHSCOPE_API_KEY"),

            # model_name="zai-org/GLM-4.6V",
            # api_base="https://api.siliconflow.cn/v1/chat/completions",
            # api_key=os.getenv("SILICONFLOW_API_KEY"),

            model_name="XiaomiMiMo/MiMo-V2-Flash:novita",
            provider="huggingface",
            api_base="https://router.huggingface.co/v1",
            api_key=os.getenv("HUGGINGFACE_API_KEY"),

            react_to_all_messages= True,
            instruction="You are a helpful AI assistant in an agent collaboration network."
        )
    agent = AIAssistant(agent_config=agent_config)

    agent.start(
            network_host=os.getenv("NETWORK_HOST"),
            network_port=int(os.getenv("NETWORK_PORT", "8700")),
            network_id=os.getenv("NETWORK_ID","cqy-eru-1")
    )
    agent.wait_for_stop()
 

