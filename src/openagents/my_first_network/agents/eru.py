import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from openagents.agents.worker_agent import WorkerAgent, EventContext, ChannelMessageContext
from openagents.models.agent_config import AgentConfig
from openai import AsyncOpenAI

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
logger = logging.getLogger(__name__)

 
class AIAssistant(WorkerAgent):
    """An AI-powered assistant agent with streaming typewriter effect"""
    
    default_agent_id = "Eru"
    default_channels = ["#Home"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize OpenAI client for streaming
        self.llm_client = None

    async def on_startup(self):
        """Register capabilities when starting"""
        await super().on_startup() 
        
        # Initialize LLM client
        self.llm_client = AsyncOpenAI(
            api_key=os.getenv("SILICONFLOW_API_KEY"),
            base_url="https://api.siliconflow.cn/v1"
        )
        
        ws = self.workspace()
        await ws.channel("Home").post(f"Hello!, I'm {self.default_agent_id}, your AI assistant with typewriter effect! How can I help you today?")
        
    async def on_direct(self, msg: EventContext):
        """Handle direct messages with AI responses"""
        ws = self.workspace()
        await ws.agent(msg.source_id).send(f"Hello {msg.source_id}!")
    
    async def on_channel_post(self, msg: ChannelMessageContext):
        """Monitor channel posts and respond with streaming typewriter effect"""
        if msg.channel != "Home":
            return
        
        # Use streaming response
        await self._stream_response(msg)
    
    async def _stream_response(self, msg: ChannelMessageContext):
        """Generate response with streaming and send as single message for typewriter effect"""
        try:
            ws = self.workspace()
            channel = ws.channel(msg.channel)
            
            # Get user message
            user_message = msg.text
            logger.info(f"Generating streaming response for: {user_message[:50]}...")
            
            # Call LLM with streaming to get response faster
            stream = await self.llm_client.chat.completions.create(
                model="zai-org/GLM-4.6V",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant in an agent collaboration network. Keep responses concise and friendly."},
                    {"role": "user", "content": user_message}
                ],
                stream=True,
                max_tokens=500
            )
            
            # Accumulate complete response
            accumulated_text = ""
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    accumulated_text += content

            
            # Send complete message once (frontend TypingText will handle typewriter effect)
            if accumulated_text:
                await channel.post(accumulated_text.strip())
                logger.info(f"Sent complete response: {len(accumulated_text)} chars")
            else:
                logger.warning("No response generated from LLM")
            
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            # Fallback to regular response
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
 

