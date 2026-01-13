"""
Eru LangChain Agent - An AI assistant powered by LangChain framework

This agent uses LangChain's streaming capabilities to provide real-time responses
in the OpenAgents network.
"""
import asyncio
import os
import logging
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# LangChain imports
# PLEASE USE THE SPECIFIC VERSIONS BELOW TO AVOID COMPATIBILITY ISSUES
# pip install "langchain==0.3.0" "langchain-community==0.3.0" "langchain-core==0.3.0" "langchain-openai==0.2.0"
try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.tools import tool
    from langchain_core.messages import HumanMessage, AIMessage
except ImportError as e:
    print(f"❌ 导入失败，具体错误信息: {e}")
    print("LangChain dependencies not installed. Install with:")
    print("  pip install langchain langchain-openai langchain-core")
    exit(1)

from openagents.agents import LangChainAgentRunner
from openagents.models.event_context import EventContext
from openagents.models.event import Event
from openagents.models.agent_config import AgentConfig

# logging.basicConfig(level=logging.DEBUG)

# Load environment variables
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

logger = logging.getLogger(__name__)


# Define tools for Eru
@tool
def get_current_time() -> str:
    """Get the current time and date."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    try:
        # Safe evaluation of mathematical expressions
        result = eval(expression, {"__builtins__": {}}, {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "len": len, "pow": pow
        })
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"


class StreamingLangChainAgentRunner(LangChainAgentRunner):
    """
    Extended LangChain Agent Runner with streaming support.
    
    This runner supports streaming responses from LangChain agents,
    sending partial updates as they arrive.
    """
    
    def __init__(self, *args, enable_streaming=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_streaming = enable_streaming
        self.greeting_sent = False
    
    def _extract_input_text(self, context: EventContext) -> str:
        """
        Extract input text from event context, with special handling for channel messages.
        
        Args:
            context: The event context
            
        Returns:
            The extracted text content
        """
        event = context.incoming_event
        payload = event.payload
        
        logger.debug(f"📋 Extracting text from event: {event.event_name}")
        
        # For channel message notifications, the structure is:
        # payload -> content -> text
        if event.event_name == "thread.channel_message.notification":
            if isinstance(payload, dict) and "content" in payload:
                content = payload.get("content", {})
                
                if isinstance(content, dict) and "text" in content:
                    text = content["text"]
                    logger.debug(f"   Found text in content.text: '{text[:50]}'")
                    return text
                elif isinstance(content, str):
                    logger.debug(f"   Found text in content (string): '{content[:50]}'")
                    return content
        
        # For direct message notifications - same structure
        if event.event_name == "thread.direct_message.notification":
            if isinstance(payload, dict) and "content" in payload:
                content = payload.get("content", {})
                
                if isinstance(content, dict) and "text" in content:
                    text = content["text"]
                    logger.debug(f"   Found text in content.text: '{text[:50]}'")
                    return text
        
        # Fallback to parent class method
        logger.debug("   Using parent class text extraction")
        return super()._extract_input_text(context)
    
    async def setup(self):
        """Setup the runner and send greeting message."""
        await super().setup()
        
        # Send greeting to #Home channel after setup
        if not self.greeting_sent:
            try:
                # Get workspace and post greeting
                messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
                if messaging:
                    await messaging.send_channel_message(
                        channel="Home",
                        text=f"Hello! I'm {self.agent_id}, your AI assistant powered by LangChain. How can I help you today?"
                    )
                    self.greeting_sent = True
                    logger.info(f"Sent greeting to #Home channel")
            except Exception as e:
                logger.error(f"Failed to send greeting: {e}")
    
    async def react(self, context: EventContext):
        """
        React to incoming messages with streaming support.
        
        This method streams responses as they are generated by the LangChain agent.
        """
        # Check if we should react to this event
        if not self._should_react(context):
            logger.debug(f"Skipped event due to filter")
            return

        try:
            # Extract input for LangChain agent
            input_text = self._extract_input_text(context)
            
            # Additional logging to debug text extraction
            logger.info(f"📝 Extracted input text: '{input_text[:200] if input_text else 'EMPTY'}'")
            logger.debug(f"   Full payload: {context.incoming_event.payload}")
            
            if not input_text:
                logger.warning("❌ No input text found in event - cannot process")
                return

            logger.info(f"✅ Processing message from {context.incoming_event.source_id}: {input_text[:100]}...")

            # Build input for LangChain agent
            langchain_input = self._build_langchain_input(context)

            # Check if streaming is enabled and supported
            if self.enable_streaming and hasattr(self._langchain_agent, 'astream'):
                await self._stream_response(context, langchain_input)
            else:
                # Fallback to non-streaming
                await self._send_complete_response(context, langchain_input)

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            await self._send_error_response(context, error_msg)
    
    async def _stream_response(self, context: EventContext, langchain_input: dict):
        """
        Stream the response from LangChain agent.
        
        Since OpenAgents doesn't support message editing, we just collect the full
        response and send it once. In the future, this could be enhanced to send
        typing indicators or progress updates.
        
        Args:
            context: The event context
            langchain_input: Input dictionary for LangChain agent
        """
        accumulated_response = ""
        
        try:
            # Show typing indicator (optional - comment out if not needed)
            # await self._send_typing_indicator(context, True)
            
            # Stream the agent's response and accumulate
            async for chunk in self._langchain_agent.astream(langchain_input):
                # Extract text from chunk
                chunk_text = self._extract_chunk_text(chunk)
                if chunk_text:
                    accumulated_response += chunk_text
                    # Log progress
                    logger.debug(f"Accumulated {len(accumulated_response)} chars...")
            
            # Hide typing indicator
            # await self._send_typing_indicator(context, False)
            
            # Send the complete response
            if accumulated_response:
                await self._send_response(context, accumulated_response)
                logger.info(f"Sent complete response: {len(accumulated_response)} chars")
            else:
                logger.warning("No response generated from LangChain agent")
            
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            # await self._send_typing_indicator(context, False)
            
            # Send whatever we have accumulated so far
            if accumulated_response:
                await self._send_response(
                    context, 
                    accumulated_response + f"\n\n_[Error: {str(e)}]_"
                )
            else:
                await self._send_error_response(context, str(e))
    
    def _extract_chunk_text(self, chunk: Any) -> str:
        """Extract text content from a streaming chunk."""
        # Handle different chunk formats
        if isinstance(chunk, dict):
            # AgentExecutor returns dict with 'output' key
            if 'output' in chunk:
                return chunk['output']
            # Or might have 'messages' key with AIMessage
            if 'messages' in chunk and chunk['messages']:
                last_msg = chunk['messages'][-1]
                if hasattr(last_msg, 'content'):
                    return last_msg.content
        elif isinstance(chunk, str):
            return chunk
        elif hasattr(chunk, 'content'):
            return chunk.content
        
        return ""
    
    async def _send_typing_indicator(self, context: EventContext, is_typing: bool):
        """
        Send typing indicator (if supported by messaging mod).
        
        Currently not implemented as OpenAgents doesn't have a standard typing indicator.
        This is a placeholder for future enhancement.
        """
        # TODO: Implement typing indicator when available
        pass
    
    async def _send_complete_response(self, context: EventContext, langchain_input: dict):
        """Send complete response without streaming."""
        # Use ainvoke or invoke
        if hasattr(self._langchain_agent, 'ainvoke'):
            result = await self._langchain_agent.ainvoke(langchain_input)
        elif hasattr(self._langchain_agent, 'invoke'):
            result = self._langchain_agent.invoke(langchain_input)
        else:
            raise ValueError("LangChain agent has no invoke method")
        
        # Extract output
        output = self._extract_output(result)
        
        # Send response
        await self._send_response(context, output)
    
    async def _send_error_response(self, context: EventContext, error_msg: str):
        """Send an error message response."""
        response_text = f"Sorry, I encountered an error: {error_msg}"
        await self._send_response(context, response_text)
    
    async def _create_response_event(self, context: EventContext, response_text: str) -> Event:
        """Create a response event for the given context."""
        source_id = context.incoming_event.source_id
        
        # Determine if this is a channel or direct message
        channel = context.incoming_event.payload.get("channel")
        
        if channel:
            # Channel message - reply in channel
            return Event(
                event_name="thread.channel_message.post",
                source_id=self.agent_id,
                relevant_mod="openagents.mods.workspace.messaging",
                destination_id=f"channel:{channel}",
                payload={
                    "channel": channel,
                    "content": {
                        "text": response_text
                    },
                    "reply_to_id": context.incoming_event.event_id,
                },
            )
        else:
            # Direct message - reply to sender
            return Event(
                event_name="agent.message",
                source_id=self.agent_id,
                destination_id=source_id,
                payload={
                    "content": {
                        "text": response_text
                    },
                    "response_to": context.incoming_event.event_id,
                },
            )


def create_eru_langchain_agent(enable_streaming: bool = True):
    """
    Create the Eru LangChain agent with tools.
    
    Args:
        enable_streaming: Whether to enable streaming responses
    
    Returns:
        Configured AgentExecutor
    """
    # Initialize the LLM with streaming support
    api_key = os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set SILICONFLOW_API_KEY or OPENAI_API_KEY")
    
    # Configure LLM with streaming
    llm = ChatOpenAI(
        model="zai-org/GLM-4.6V",
        api_key=api_key,
        base_url="https://api.siliconflow.cn/v1",
        temperature=0.7,
        streaming=enable_streaming,  # Enable streaming
    )
    
    # Define tools
    tools = [get_current_time, calculate]
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are Eru, a helpful AI assistant in the OpenAgents network. "
            "You can help with various tasks and answer questions. "
            "Be friendly, concise, and helpful. "
            "If you're in the #Home channel, engage naturally with the conversation."
        ),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create the agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # Wrap in AgentExecutor
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # Set to False in production
        handle_parsing_errors=True,
    )
    
    return executor


def main():
    """Main entry point for Eru LangChain agent."""
    print("=" * 60)
    print("Eru - LangChain Powered AI Assistant")
    print("=" * 60)
    
    # Check for API key
    if not (os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")):
        print("\n⚠️  Warning: No API key found!")
        print("Set SILICONFLOW_API_KEY or OPENAI_API_KEY environment variable")
        return
    
    # Create the LangChain agent
    print("\n1. Creating LangChain agent...")
    try:
        langchain_agent = create_eru_langchain_agent(enable_streaming=True)
        print("   ✓ LangChain agent created with tools: get_current_time, calculate")
    except Exception as e:
        print(f"   ✗ Failed to create agent: {e}")
        return
    
    # Create the OpenAgents runner with streaming support
    print("\n2. Creating StreamingLangChainAgentRunner...")
    
    # Event filter with correct payload structure
    def debug_event_filter(ctx):
        """Filter that accepts Home channel messages and direct messages."""
        event = ctx.incoming_event
        payload = event.payload
        
        # Log event info
        logger.info(f"🔍 Event Filter:")
        logger.info(f"   Event: {event.event_name}")
        logger.info(f"   Source: {event.source_id}")
        
        # Check if it's a channel message notification
        if event.event_name == "thread.channel_message.notification":
            # The payload structure is: payload -> channel (direct, no nesting)
            if isinstance(payload, dict):
                channel = payload.get("channel")
                # Note: sender info may be in event.source_id
                sender_id = event.source_id
                
                logger.info(f"   Channel: {channel}")
                logger.info(f"   Sender: {sender_id}")
                
                # Don't respond to our own messages
                if sender_id == "Eru":
                    logger.info(f"   ❌ Skipping: our own message")
                    return False
                
                # Accept if channel is "Home" (without #)
                if channel == "Home":
                    logger.info(f"   ✅ Accepting: Home channel message")
                    return True
                else:
                    logger.info(f"   ❌ Skipping: not Home channel (got: {channel})")
                    return False
            else:
                logger.warning(f"   ⚠️  Payload is not a dict: {type(payload)}")
                return False
        
        # Accept direct messages
        if event.event_name == "thread.direct_message.notification":
            sender_id = event.source_id
            if sender_id == "Eru":
                logger.info(f"   ❌ Skipping: our own DM")
                return False
            logger.info(f"   ✅ Accepting: direct message")
            return True
        
        logger.info(f"   ❌ Skipping: unknown event type")
        return False
    
    runner = StreamingLangChainAgentRunner(
        langchain_agent=langchain_agent,
        agent_id="Eru",
        include_network_tools=False,  # Don't include network tools to avoid confusion
        enable_streaming=True,
        event_filter=debug_event_filter,
    )
    print(f"   ✓ Runner created with agent_id: {runner.agent_id}")
    
    # Connect to the network
    print("\n3. Connecting to OpenAgents network...")
    network_host = os.getenv("NETWORK_HOST", "localhost")
    network_port = int(os.getenv("NETWORK_PORT", "8700"))
    network_id = os.getenv("NETWORK_ID", "cqy-eru-1")
    
    print(f"   Host: {network_host}")
    print(f"   Port: {network_port}")
    print(f"   Network ID: {network_id}")
    
    try:
        runner.start(
            network_host=network_host,
            network_port=network_port,
            network_id=network_id,
            # transport="http",  # Force HTTP transport to avoid gRPC dependency issues
        )
        print("   ✓ Connected successfully!")
        print("\n" + "=" * 60)
        print("🤖 Eru is now online and listening!")
        print("   - Responds to messages in #Home channel")
        print("   - Responds to direct messages")
        print("   - Streaming responses enabled")
        print("\nPress Ctrl+C to stop")
        print("=" * 60 + "\n")
        
        # Wait for the agent to be stopped
        runner.wait_for_stop()
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Eru...")
        runner.stop()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"Make sure the OpenAgents network is running on {network_host}:{network_port}")


if __name__ == "__main__":
    # Set logging level
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()
