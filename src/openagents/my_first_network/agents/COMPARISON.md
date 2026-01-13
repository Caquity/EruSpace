# Eru实现对比：原版 vs LangChain版

## 代码对比

### 原版 Eru (WorkerAgent)

```python
from openagents.agents.worker_agent import WorkerAgent, EventContext, ChannelMessageContext

class AIAssistant(WorkerAgent):
    """An AI-powered assistant agent"""
    
    default_agent_id = "Eru"
    default_channels = ["#Home"]

    async def on_startup(self):
        """启动时发送问候"""
        ws = self.workspace()
        await ws.channel("Home").post(
            f"Hello!, I'm {self.default_agent_id}, your AI assistant."
        )
        
    async def on_direct(self, msg: EventContext):
        """处理直接消息"""
        ws = self.workspace()
        await ws.agent(msg.source_id).send(f"Hello {msg.source_id}!")
    
    async def on_channel_post(self, msg: ChannelMessageContext):
        """处理频道消息"""
        if msg.channel != "Home":
            return
        
        await self.run_agent(
            context=msg,
            instruction="Reply to the message with a short response"
        )

# 启动
agent = AIAssistant(agent_config=agent_config)
agent.start(network_host="localhost", network_port=8700)
agent.wait_for_stop()
```

**特点**:
- ✅ 简洁直观
- ✅ 高度集成OpenAgents
- ✅ 少量代码
- ❌ 依赖特定框架
- ❌ 工具系统不够灵活

---

### LangChain版 Eru

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from openagents.agents import LangChainAgentRunner

# 定义工具
@tool
def get_current_time() -> str:
    """Get the current time and date."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 创建LangChain agent
llm = ChatOpenAI(model="gpt-4", streaming=True)
tools = [get_current_time]
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# 创建OpenAgents runner
class StreamingLangChainAgentRunner(LangChainAgentRunner):
    async def setup(self):
        await super().setup()
        # 发送问候
        messaging = self.client.mod_adapters.get("openagents.mods.workspace.messaging")
        await messaging.send_channel_message(
            channel="Home",
            text=f"Hello! I'm {self.agent_id}, your AI assistant."
        )
    
    async def react(self, context: EventContext):
        # 流式处理响应
        accumulated = ""
        async for chunk in self._langchain_agent.astream(input):
            accumulated += self._extract_chunk_text(chunk)
        await self._send_response(context, accumulated)

# 启动
runner = StreamingLangChainAgentRunner(
    langchain_agent=executor,
    agent_id="Eru",
    event_filter=lambda ctx: ctx.channel == "Home" or ctx.is_direct
)
runner.start(network_host="localhost", network_port=8700)
runner.wait_for_stop()
```

**特点**:
- ✅ 强大的工具系统
- ✅ 流式处理支持
- ✅ 标准化框架
- ✅ 易于扩展
- ❌ 代码较复杂
- ❌ 依赖更多

---

## 详细功能对比

### 1. 消息处理

#### 原版
```python
async def on_channel_post(self, msg: ChannelMessageContext):
    if msg.channel != "Home":
        return
    
    await self.run_agent(
        context=msg,
        instruction="Reply to the message"
    )
```

#### LangChain版
```python
async def react(self, context: EventContext):
    if not self._should_react(context):
        return
    
    input_text = self._extract_input_text(context)
    langchain_input = self._build_langchain_input(context)
    
    async for chunk in self._langchain_agent.astream(langchain_input):
        accumulated += self._extract_chunk_text(chunk)
    
    await self._send_response(context, accumulated)
```

### 2. 工具定义

#### 原版（通过配置）
```python
agent_config = AgentConfig(
    model_name="gpt-4",
    instruction="You are a helpful AI assistant."
)
# 工具通过run_agent自动注入
```

#### LangChain版（显式定义）
```python
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a location."""
    return f"Weather in {location}: Sunny"

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression))

tools = [get_weather, calculate]
agent = create_tool_calling_agent(llm, tools, prompt)
```

### 3. 启动配置

#### 原版
```python
agent = AIAssistant(agent_config=agent_config)
agent.start(
    network_host="localhost",
    network_port=8700,
    network_id="cqy-eru-1"
)
```

#### LangChain版
```python
runner = StreamingLangChainAgentRunner(
    langchain_agent=executor,
    agent_id="Eru",
    include_network_tools=False,
    enable_streaming=True,
    event_filter=lambda ctx: (
        ctx.incoming_event.payload.get("message", {}).get("channel") == "Home"
        or ctx.incoming_event.event_name == "thread.direct_message.notification"
    )
)
runner.start(network_host="localhost", network_port=8700)
```

---

## 性能对比

| 指标 | 原版 | LangChain版 |
|------|------|-------------|
| 启动时间 | ~2秒 | ~3秒 |
| 内存占用 | ~100MB | ~150MB |
| 响应延迟 | ~1-2秒 | ~1-2秒 |
| 代码行数 | ~50行 | ~450行 |
| 依赖数量 | 2个 | 5个 |

---

## 使用场景建议

### 选择原版Eru，如果你：
- ✅ 需要快速原型开发
- ✅ 只使用OpenAgents生态
- ✅ 不需要复杂的工具系统
- ✅ 代码简洁优先

### 选择LangChain版Eru，如果你：
- ✅ 需要强大的工具系统
- ✅ 想要标准化的agent框架
- ✅ 需要流式输出能力
- ✅ 计划与LangChain生态集成
- ✅ 需要更细粒度的控制

---

## 迁移指南

### 从原版迁移到LangChain版

1. **安装依赖**
```bash
pip install langchain langchain-openai langchain-core
```

2. **转换on_channel_post**
```python
# 原版
async def on_channel_post(self, msg):
    await self.run_agent(context=msg, instruction="Reply")

# LangChain版
# 直接使用StreamingLangChainAgentRunner
# 它会自动处理频道消息
```

3. **转换工具**
```python
# 原版：通过agent_config配置

# LangChain版：显式定义
@tool
def my_tool(arg: str) -> str:
    """Tool description"""
    return result
```

4. **启动代码**
```python
# 原版
agent = AIAssistant(agent_config=config)

# LangChain版
langchain_agent = create_eru_langchain_agent()
runner = StreamingLangChainAgentRunner(
    langchain_agent=langchain_agent,
    agent_id="Eru"
)
```

---

## 总结

两个版本各有优势，选择取决于你的需求：

- **原版**：简单、快速、OpenAgents原生
- **LangChain版**：强大、灵活、标准化

对于学习和快速开发，推荐**原版**  
对于生产环境和复杂需求，推荐**LangChain版**
