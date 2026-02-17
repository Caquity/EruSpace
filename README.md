
![EruSpace](src/openagents/my_first_network/img/EruSpace.png)

> 基于 OpenAgents 框架的多智能体协作网络系统
---

![Certificate](src/openagents/my_first_network/img/Certificate.PNG)
![Details](src/openagents/my_first_network/img/Program_Detail.png)
[EruSpace - OpenAgents官网链接](https://openagents.org/zh/showcase/hackathon-2025/28)
[演示视频](https://www.bilibili.com/video/BV1zSvCBrEFq/)

---

## 1. 项目概述

### 项目名称与 Network ID
- **项目名称**: `EruSpace`
- **Network ID**: `cqy-eru-1`
- **网络模式**: Centralized (中心化)

**EruSpace** 是一个基于 OpenAgents 框架构建的生产级多智能体协作网络，集成了 AI 助手、新闻聚合、智能评论等功能，通过多通道消息系统实现智能体间的高效协作。

### 目标用户/使用场景

**目标用户**:
- AI 开发者：学习和实践多智能体系统开发
- 内容创作者：获取实时新闻资讯和 AI 辅助
- 研究人员：探索智能体协作模式和通信机制
- 企业团队：构建自动化信息流和智能助手系统

**核心使用场景**:
1. **智能对话助手**: 在 `#Home` 频道提供 24/7 AI 问答服务
2. **新闻聚合与分发**: 通过 ntfy 推送所集成的开源项目：TrendRadar，自动获取和分发新闻
3. **智能内容评论**: AI 评论员对新闻内容进行风趣点评和摘要
4. **多智能体协作演示**: 展示智能体间的消息传递、触发机制和协作模式

---

## 2. 技术架构

### 使用的 OpenAgents 版本与相关技术栈

**OpenAgents 框架**:
- 版本要求: `>=0.7.0`
- 核心组件:
  - `WorkerAgent`: 基础智能体类，处理事件驱动逻辑
  - `CollaboratorAgent`: 声明式 YAML 智能体类
  - `AgentConfig`: 智能体配置系统
  - `Workspace Messaging Mod`: 多通道消息系统

**技术栈**:
- **编程语言**: Python 3.12
- **通信协议**:
  - HTTP (端口 8700) - Studio + MCP + API
  - gRPC (端口 8600) - 高性能智能体通信
    
- **外部服务集成**:
  - ntfy.sh - 推送通知服务 ⭐️
  - [TrendRadar - 热点助手 —— 告别无效刷屏，只看真正关心的新闻资讯](https://github.com/sansan0/TrendRadar.git)  ⭐️
  - Brave Search API - 辅助搜索
  - 新增 `HUGGINGFACE_API_KEY` 支持 ⭐️
  - 新增 `SILICONFLOW_API_KEY` 支持 ⭐️
 
- **功能扩展**:
  - [流式响应](#流式响应) ⭐️

    
- **部署方式**:
  - Docker 容器化
  - 云平台支持 (Zeabur)

### Agent Network 设计思路

**设计原则**:
1. **事件驱动架构**: 智能体通过事件触发响应，而非轮询
2. **模块化设计**: 智能体、工具、Mod 分离，便于扩展
3. **频道隔离**: 不同功能区分到独立频道，避免信息混乱
4. **共享存储**: 通过共享文件系统实现智能体间数据交换
5. **多模态支持**: 同时支持 Python 代码智能体和 YAML 声明式智能体

**核心组件交互**:

<img src="src/openagents/my_first_network/img/Architect.png" width="50%">

### 系统流程图

**新闻流转流程**:

<img src="src/openagents/my_first_network/img/System.png" width="50%">

---

## 3. 智能体设计

### Agent 1: Eru

通用对话助手，`#Home` 频道

- **核心功能**:
  - 响应所有 `#Home` 频道消息
  - 提供 AI 问答服务
  - 支持直接消息 (DM) 交互


- 多 LLM 提供商支持 (HuggingFace/SiliconFlow/Groq)
- 环境变量灵活配置
- 频道级别消息过滤

---

### Agent 2: Eru-news & Eru-alter

基于 **TrendRadar** 推送的新闻聚合,分发助手与评论者

- **核心功能**:
  1. **被动响应**: 响应 @mention 触发
  2. **主动通知**: 每小时检查新闻更新并通知
  3. **去重机制**: 避免重复发送相同新闻
  4. **存储管理**: 发送后自动清理已读新闻

- **共享存储模式**: 与 `ntfy_listener`通过文件系统共享数据
- **状态追踪**: `sent_news.json` 记录发送历史
- **智能提示**: 根据时间间隔给出不同提示信息
- **容错设计**: 监听器未运行时给出明确提示

- 监听 `Eru-news` 的新闻发布
- 过滤无价值信息，提取关键内容

---

### 多 Agent 协作机制

**通信方式**:
1. **频道广播**: 智能体在频道发布公开消息
2. **@mention 触发**: 通过 `@agent_id` 触发特定智能体
3. **Reply 链**: 支持消息回复链，形成对话树
4. **Direct Message**: 智能体间私密通信

**协作流程示例**:
```
用户 → @news-assistant (mention)
  ↓
Eru-news → 读取 latest_news.json
  ↓
Eru-news → 发布格式化新闻到 #News-board
  ↓
Eru-alter → 检测到 Eru-news 的消息
  ↓
Eru-alter → 生成点评并回复
  ↓
用户 ← 收到新闻 + 点评
```

**使用的 OpenAgents 高级特性**:
1. **Workspace Messaging Mod**: 
   - 多频道系统
   - 消息路由
   - Thread 管理
   
2. **Shared Cache Mod**:
   - 智能体间共享数据
   - 避免重复计算
   
3. **事件驱动系统**:
   - `on_channel_post()` - 频道消息事件
   - `on_channel_mention()` - 提及事件
   - `on_channel_reply()` - 回复事件
   - `on_direct()` - 私信事件
   
4. **混合智能体类型**:
   - Python `WorkerAgent` - 复杂逻辑
   - YAML `CollaboratorAgent` - 快速配置

---

## 4. 协作场景与创新点

### 核心协作场景
**1: 通用助手**
1.负责日常会话

**2: 新闻聚合与智能评论**

**流程描述**:
1. `ntfy_listener` 持续监听 **TrendRadar **推送通知
2. 收到新闻后存储到共享 JSON 文件
3. `Eru-news` 每小时检查一次更新，发现新内容后在 `#News-board` 发布通知
4. 用户 **@Eru-news** 触发新闻查询
5. `Eru-news` 回复格式化的新闻内容
6. `Eru-alter` 检测到 `Eru-news` 的消息，自动生成点评
7. 用户同时获得原始新闻 + AI 评论

---

**Easter Egg🥚: Multi-Agent Communication**

**演示场景** (EASTER-EGG 频道):
- `stuff 🤠`: AI 创作解决方案顾问
- `client`: 新手网文作者角色

- **角色扮演**: 模拟真实业务场景
- **对抗性对话**: client 持续质疑，推动深度讨论
- **情境化学习**: 通过对话展示复杂产品功能

---

### 创新性体现

#### 1. 任务分配机制

**智能体职责分离**:

- **Eru**: 通用能力 
- **Eru-news**: 专业领域
- **Eru-alter**: 内容加工

#### 2. 混合触发机制

**主动 + 被动结合**:

```python
# 被动响应 (on-demand)
async def on_channel_mention(self, msg):
    # 用户明确请求时才响应
    await self._get_latest_news_message()

# 主动通知 (proactive)
async def _check_news_loop(self):
    while True:
        # 定期检查并主动通知
        await self._check_for_new_news()
        await asyncio.sleep(3600)
```

#### 3. 去重与状态管理

**文件系统作为状态存储**:

```python
# 新闻存储
latest_news.json         # 当前待发送新闻
sent_news.json           # 发送历史记录
news_sent_marker.json    # 发送标记

# 状态转换
新闻到达 → 写入 latest_news.json
用户查询 → 读取并发送
发送成功 → 写入 sent_news.json + 删除 latest_news.json
```

#### 4. 异常处理

**多层容错设计**:
```python
# 1. ntfy_listener 未运行
if not self.NEWS_STORAGE_FILE.exists():
    return "请确保 ntfy listener 正在运行..."

# 2. 新闻已发送
if news_id == self.last_sent_news_id:
    return f"新闻已发送，{minutes_left}分钟后更新"

# 3. 网络超时
agent_config = AgentConfig(
    request_timeout=120,  # 云部署超时保护
    ...
)
```

---

## 5. 实际应用价值

**1: 集成外部项目：TrendRadar**

- ntfy 推送集成，精选信息源
- AI 评论员过滤噪音，提取精华
- 定时推送避免信息轰炸

**2: 单一 AI 局限性**

- 多智能体分工协作
- 不同模型处理不同任务 (Kimi 推理 vs SiliconFlow 对话)
- 专业领域智能体 (新闻 vs 对话)

### 可扩展性

**垂直扩展**:
 **增强单个智能体能力**:
   - RAG (检索增强生成)

**未来延伸方向**:
- **跨网络协作**: 连接多个 OpenAgents 网络

---

## 6. 开发、发布与使用说明

### 环境依赖

**系统要求**:
- **操作系统**: Linux / macOS / Windows (WSL)
- **Python 版本**: 3.12
- **Docker** (可选): 用于容器化部署
- **网络**: 需要访问 LLM API 服务

**核心依赖**:
```bash
openagents>=0.7.0
python-dotenv
requests
asyncio
```

**可选依赖**:

- Brave Search API Key (新闻搜索)
- ntfy.sh 账号 (推送通知)
- `Huggingface_hub`

---

### 安装与运行步骤

#### 本地开发模式

**Step 1: 克隆代码**

```bash
git clone <repository_url>
cd openagents
```

**Step 2: 配置环境变量**

```bash
# 环境变量(Optional)
DASHSCOPE_API_KEY=
API_BASE_URL=
BRAVE_API_KEY=
HUGGINGFACE_API_KEY= (available)
SILICONFLOW_API_KEY= (available)
```

**Step 3: 启动网络**
```bash
# 启动 OpenAgents 网络
openagents network start \
  src/openagents/my_first_network/network.yaml
```

**Step 4: 启动智能体**
```bash
# 终端 1: 启动 Eru 
python src/openagents/my_first_network/agents/eru.py
# 终端 2: 启动Eru-news
python src/openagents/my_first_network/agents/news_assistant_ntfy.py
# 终端 3: 启动Eru-alter
openagents agent start \
  src/openagents/my_first_network/agents/commentator.yaml
```

**Step 5: 启动辅助工具 (可选)**

```bash
# 终端 4: ntfy 监听器
python src/openagents/my_first_network/tools/ntfy_listener.py
```

**Step 6: 访问 Studio**
```bash
# 浏览器打开
http://localhost:8700/studio/
```

---

#### 云平台部署 (Zeabur)

**Step 1: 推送到 GitHub**

```bash
git add .
git commit -m "Deploy EruSpace"
git push origin main
```

**Step 2: 连接云平台**
- 在 Zeabur 控制台导入 GitHub 仓库
- 选择 Dockerfile 构建方式

**Step 3: 配置环境变量**
在云平台环境变量设置页面添加:

```
HUGGINGFACE_API_KEY=hf_xxxxx
DASHSCOPE_API_KEY=sk_xxxxx
NETWORK_HOST=localhost
NETWORK_PORT=8700
```

**Step 4: 部署**

- 云平台自动构建镜像并部署
- 获取公网访问地址: `https://your-app.zeabur.app/studio/`

---

### 关键配置

#### API 密钥配置

**可选密钥**:

```bash
SILICONFLOW_API_KEY
HUGGINGFACE_API_KEY
```

------

## 8. 挑战与解决方案

### 流式响应

- OpenAgents目前不支持消息更新（没有`update_message` API），因此采用了**流式分块发送**的方案。

**流式响应处理**：
```python
async def _stream_response(self, msg: ChannelMessageContext):
    # 调用LLM流式API
    stream = await self.llm_client.chat.completions.create(
        model="zai-org/GLM-4.6V",
        messages=[...],
        stream=True,
        max_tokens=500
    )
    
    # 累积文本并定期发送
    accumulated_text = ""
    chunk_buffer = ""
    chunk_size = 20  # 每20个字符发送一次
    
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            chunk_buffer += content
            accumulated_text += content
            
            # 达到阈值时发送块
            if len(chunk_buffer) >= chunk_size:
                await channel.post({
                    "text": chunk_buffer,
                    "is_streaming": True,
                    "stream_id": msg.message_id
                })
                chunk_buffer = ""
                await asyncio.sleep(0.1)  # 增加打字机效果的延迟
```

**优势**：
- ✅ 真实的流式响应，用户可以实时看到AI思考过程
- ✅ 可配置的块大小和延迟，调整打字速度
- ✅ 支持错误处理和降级

**前端实现**：
- 使用现有的`TypingText`组件为特定发送者（Eru）的消息添加打字机效果。


---

### 2: 智能体间数据共享

- ntfy_listener 是独立 Python 进程
- news_assistant 是 OpenAgents WorkerAgent
- 两者需要共享实时新闻数据

**尝试**:

1. ❌ 数据库 - 过于重量级
2. ❌ Redis - 增加部署复杂度
3. ✅ **文件系统共享**

**解决方案**:

```python
# tools/ntfy_listener.py
class NtfyNewsStorage:
    STORAGE_FILE = Path(__file__).parent / "latest_news.json"
    
    @classmethod
    def save_news(cls, news_data: dict):
        with open(cls.STORAGE_FILE, 'w') as f:
            json.dump(news_data, f)

# agents/news_assistant_ntfy.py
news = NtfyNewsStorage.load_news()
```

---

### 3: 防止消息重复发送

**问题描述**:
- 用户多次 @mention 时不应重复发送相同新闻
- 智能体重启后应记住已发送的新闻

**解决方案**:
```python
# 双文件状态管理
latest_news.json      # 当前待发送新闻
sent_news.json        # 历史记录

# 发送逻辑
if news_id == self.last_sent_news_id:
    if time_since_last_check < 1_hour:
        return "新闻已发送，稍后更新"

# 发送后清理
self.last_sent_news_id = news_id
NtfyNewsStorage.mark_as_sent(news_id)  # 删除 latest_news.json
```

---

## 9. 未来展望
1. 更多快速接口，接入各类开源项目
2. 快速搭建独立RAG库，这正做的每个智能体的独特性


## 相关资源

**官方文档**:
- OpenAgents: https://openagents.org/docs/
- OpenAgents GitHub: https://github.com/openagents-org/openagents

**API 文档**:
- HuggingFace Inference: https://huggingface.co/docs/api-inference
- DashScope (Qwen): https://help.aliyun.com/zh/dashscope/
- TrendRadar: https://github.com/sansan0/TrendRadar.git
- ntfy.sh: https://docs.ntfy.sh/
- Brave Search: https://brave.com/search/api/

**社区资源**:

- openagents示例项目: `demos/` 目录
- openagents博客文章: `changelogs/blogs/`
