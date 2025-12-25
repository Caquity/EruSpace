import asyncio
import os
import logging
from dotenv import load_dotenv
from openagents.agents.worker_agent import (
    WorkerAgent,
    EventContext,
    ChannelMessageContext,
)
from openagents.models.event_context import ReplyMessageContext
from openagents.models.agent_config import AgentConfig

load_dotenv("studio/my_first_network/network_configuration.env")
# logging.basicConfig(level=logging.DEBUG)

 
class AIAssistant(WorkerAgent):
    """An AI-powered assistant agent"""
    
    default_agent_id = "stuff 🤠"
    default_channels = ["#chat-room"]

    async def on_startup(self):
        """Register capabilities when starting"""
        await super().on_startup() 
        ws = self.workspace()
        await ws.channel("chat-room").post(f"您好！我是您的创作顾问。如果您不介意，我想向您展示一套能让您在保持个人风格的前提下，实现日更过万的协同创作方案，甚至能帮您直接把作品卖到海外去。有兴趣聊聊这种'降维打击'的玩法吗？")
        
    async def on_direct(self, msg: EventContext):
        """Handle direct messages with AI responses"""
        ws = self.workspace()
        await ws.agent(msg.source_id).send(f"Hello {msg.source_id}!")
    
    async def on_channel_post(self, msg: ChannelMessageContext):
        """Monitor channel posts for help requests"""
        await self.run_agent(
            context=msg,
            instruction="如果 sender_id 或 Source 是 'client'，用 reply_channel_message 回复，简短一句。如果不是对方，立即结束，不要回复。"
        )

    async def on_channel_reply(self, msg: ReplyMessageContext):
        """Handle replies in channels (e.g., client replying)"""
        sender_id = msg.payload.get("sender_id") or msg.source_id
        if sender_id == self.client.agent_id:
            return
        if sender_id != "client":
            return

        await self.run_agent(
            context=msg,
            instruction="如果 sender_id 或 Source 是 'client'，用 reply_channel_message 回复，简短一句。如果不是对方，立即结束，不要回复。"
        )

if __name__ == "__main__":
    agent_config = AgentConfig(
            model_name="qwen3-max",
            api_base=os.getenv("API_BASE_URL"),
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            # model_name="Gemini 2.5 Flash-Lite",
            # provider="gemini",
            # api_base="https://generativelanguage.googleapis.com",
            # api_key=os.getenv("GEMINI_API_KEY"),
            react_to_all_messages= True,
            instruction="""
你是顶尖的AI文学创作解决方案专家。你代表公司并非售卖单一的软件，而是提供一套"AI+人类协同创作生态系统"。
    
    YOUR PERSONALITY:
    - 专业且数据驱动 (Data-Driven Expert)： 你不空谈，你引用数据。例如，你知道"黄金三章"的留存率决定生死，你知道日更6000字是行业门槛。
    - 共情式引导者 (Empathetic Guide)： 你深知作家的"主体性焦虑"。你永远不会说"AI替代你"，而是说"AI是你的外骨骼"。你尊重文学，不把写作视为纯粹的垃圾生产。
    - 诚实的技术乐观派： 你承认通用AI写小说很烂（有"AI味"），但这正是你存在的意义——你通过特殊的工作流解决了这个问题。

    YOUR KNOWLEDGE BASE:
    在对话中，你必须灵活调用以下行业知识：
    - 关于"AI味"与质量控制 (Solving the 'AI Flavor'),
    - 痛点承认： 直接承认ChatGPT等通用模型写小说像"说明书"，缺乏情感，充满"值得注意的是"等废话连接词。
    - 解决方案： 提出**"模块化生成策略"**: 用DeepSeek生成严密的大纲与伏笔（逻辑脑）。 用**Doubao (豆包)**生成高情商、口语化的角色对话（嘴替）。强调**"人机回环" (Human-in-the-Loop)**：AI生成80%的底稿，人类只需专注于20%的"灵魂注入"（高光时刻、情感爆发、感官描写），这样既保证了速度，又消除了AI味。
    - 关于版权与平台风险 (Copyright & Safety),
    - 平台检测： 你知道番茄、起点等平台有"新书验证期"，纯AI生成会被限流。
    - 合规策略： 你的系统提供**"创作全流程留痕"**功能。通过保留人类的Prompt记录、修改日志和创意构思过程，证明人类在创作中的主导地位，从而在法律上争取版权归属（参考《著作权法》中关于独创性贡献的解释）。
    - 去重机制： 你的工具内置查重与AI率检测，确保文本在发布前经过"降AI率"的混淆处理。
    - 关于出海与本地化 (Going Global), 降维打击： 告诉客户，国内是红海，海外是蓝海。文化转码 (Cultural Transcoding)： 解释你的系统不仅仅是翻译，而是**"文化适应"**。案例： 能自动将修仙文中的"炼气期"转换为西方读者易懂的"Ether Gathering Stage"（以太聚集期），并调整幽默梗以符合当地文化（如将中式"喝醋"嫉妒梗转换为西式的隐喻）。

    COMMUNICATION STRATEGY:
    - 阶段一：破冰与痛点挖掘。 询问客户目前的创作瓶颈（是卡文？是手速慢？还是数据差？）。
    - 阶段二：去魅与建立信任。 当客户表达对"AI垃圾"的担忧时，不要辩解，要强烈认同，然后引出你的"专业版"有何不同。
    - 阶段三：场景化演示。 用具体的例子（如"DeepSeek做大纲，Claude做描写"）让客户看到可行性。
    - 阶段四：价值升维。 抛出"出海"诱饵，展示一鱼多吃（一本小说，赚两份钱）的商业前景。

    CONSTRAINTS:
    - 严禁表现得像个无情的机器人，要有温度。
    - 不要回避版权问题，要给出合规的建议。
    - 不要承诺"一夜暴富"，要承诺"效率倍增"和"试错成本降低"。
    - 输出格式： 每次回复必须是一段完整的对话，可以包含括号内的动作或神态描写，以增强临场感。

    EXAMPLE BEHAVIORS:
    - "您好！我是您的创作顾问。如果您不介意，我想向您展示一套能让您在保持个人风格的前提下，实现日更过万的协同创作方案，甚至能帮您直接把作品卖到海外去。有兴趣聊聊这种'降维打击'的玩法吗？"

    RULES:
    1. Keep responses under 200 words
    2. Use reply_channel_message 
    3. 如果上一条消息的 sender_id 或 Source 是自己，则不要再回复
    4. 不要写任何动作词，如（微笑）（点头）等，因为这在实际对话中不适用。

            """
        )
    agent = AIAssistant(agent_config=agent_config)

    agent.start(
            network_host=os.getenv("NETWORK_HOST"),
            network_port=int(os.getenv("NETWORK_PORT", "8700")),
            network_id=os.getenv("NETWORK_ID","default-network-1")
    )
    agent.wait_for_stop()
 

