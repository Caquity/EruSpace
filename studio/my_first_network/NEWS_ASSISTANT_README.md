# News Assistant Agent

一个基于提及触发的 AI 和旅游新闻助手，遵循 OpenAgents 开发模式。

## 📁 文件架构

```
studio/my_first_network/
├── agents/
│   └── news_assistant.py          # 新闻助手 Agent (主程序)
└── tools/
    ├── __init__.py                # 工具包初始化
    └── news_search.py             # Brave 搜索工具集
```

## 🎯 设计理念

### 1. **遵循 OpenAgents 开发模式**

参考文件：`demos/02_tech_news_stream/agents/news_hunter.py`

**继承关系**：
```python
class NewsAssistantAgent(WorkerAgent):
    """继承 WorkerAgent 基类"""
```

**核心特性**：
- ✅ 使用 `WorkerAgent` 基类
- ✅ 实现 `on_startup()`, `on_direct()`, `on_channel_post()` 生命周期方法
- ✅ 通过 `workspace()` API 进行消息发送
- ✅ 使用 `async_start()` 和 `async_stop()` 管理生命周期

### 2. **工具层设计**

参考文件：`demos/03_research_team/tools/web_search.py`

**BraveSearchClient 类**：
```python
class BraveSearchClient:
    """Brave Search API 客户端封装"""
    
    @classmethod
    def from_env(cls):
        """从环境变量创建客户端"""
    
    def search(self, query, count, freshness):
        """执行搜索"""
```

**特点**：
- ✅ 只使用 Brave Search API（无 DuckDuckGo 回退）
- ✅ 环境变量配置 (`BRAVE_API_KEY`)
- ✅ 使用 `requests` 库而非直接 HTTP
- ✅ 结构化的搜索结果返回

### 3. **消息格式化**

参考：`demos/02_tech_news_stream/tools/news_fetcher.py`

**输出样式**：
```
📰 Daily AI & Travel Brief — 2025-12-11

🤖 AI Technology News

### Hacker News · AI

1. **Article Title** (2 hours ago)
   🔗 https://example.com
   Article description...

✈️ Travel & Tourism News

### National Geographic Travel

1. **Travel Story** (1 day ago)
   🔗 https://example.com
   Story description...
```

## 🚀 使用方法

### 前提条件

1. **配置环境变量**：
```bash
# 在 studio/my_first_network/network_configuration.env 中添加
BRAVE_API_KEY=your_brave_api_key_here
NETWORK_HOST=localhost
NETWORK_PORT=8700
NETWORK_ID=default-network-1
```

2. **获取 Brave API Key**：
   - 访问 https://brave.com/search/api/
   - 注册并获取 API 密钥

### 启动 Agent

```bash
cd /Users/conqury/openagents/studio/my_first_network/agents

# 方式 1: 使用环境变量
python news_assistant.py

# 方式 2: 命令行参数
python news_assistant.py --host localhost --port 8700 --network-id main
```

### 使用 Agent

**1. 在频道中提及**：
```
在 #general 频道发送:
@news-assistant 给我看看今天的新闻

或者:
Hey @news-assistant, what's new in AI?
```

**2. 直接消息**：
```
直接给 news-assistant 发送任何消息
都会收到当天的新闻摘要
```

## 📊 功能特性

### AI 科技新闻源
- 🔶 Hacker News AI 相关话题
- 🤖 Reddit r/MachineLearning
- 🧠 Reddit r/artificial

### 旅游新闻源
- 🌍 National Geographic Travel
- 📱 小红书旅游攻略
- 🐦 新浪微博旅游热门

### 智能特性
- ⚡ 按需触发（提及时才响应）
- 💾 1小时缓存（避免重复请求）
- 🎯 多种提及格式支持
- 🔄 异步处理（不阻塞事件循环）
- 📅 自动标注日期

## 🔧 技术实现

### 1. 提及检测
```python
def _is_mentioned(text: str) -> bool:
    """检测多种提及格式"""
    patterns = [
        "@news-assistant",
        "@news_assistant", 
        "news-assistant",
        "news assistant",
    ]
    return any(pattern in text.lower() for pattern in patterns)
```

### 2. 缓存机制
```python
async def _get_daily_digest(self) -> str:
    """带缓存的摘要生成"""
    # 1小时内使用缓存
    if cache_valid:
        return cached_digest
    
    # 在线程池中生成新摘要（避免阻塞）
    digest = await asyncio.to_thread(generate_daily_digest)
    return digest
```

### 3. 消息发送
```python
# 使用 OpenAgents workspace API
ws = self.workspace()

# 频道消息（带提及）
await ws.channel(channel).post_with_mention(
    digest,
    mention_agent_id=sender_id
)

# 直接消息
await ws.agent(sender_id).send(digest)
```

## 🆚 与 news_hunter 的区别

| 特性 | news_hunter | news_assistant |
|------|-------------|----------------|
| 触发方式 | 60秒轮询 | 提及触发 |
| 消息类型 | 单条新闻 | 每日摘要 |
| 新闻源 | Hacker News | 多源（AI + 旅游）|
| 缓存机制 | URL去重 | 时间缓存 |
| 交互方式 | 被动推送 | 主动请求 |

## 📝 开发思想总结

### 符合 OpenAgents 模式
1. **分层架构**：Agent 层 + 工具层分离
2. **事件驱动**：基于 `on_*` 方法响应事件
3. **异步优先**：使用 `async/await` 处理 I/O
4. **Workspace API**：通过 `workspace()` 进行通信

### 遵循项目约定
1. **路径处理**：使用 `sys.path.insert` 模式
2. **环境配置**：使用 `dotenv` 加载配置
3. **错误处理**：完整的异常捕获和日志
4. **命令行接口**：支持 `argparse` 参数

### 最佳实践
1. **资源管理**：正确的启动/关闭生命周期
2. **性能优化**：缓存机制和线程池
3. **用户体验**：清晰的日志和状态提示
4. **可扩展性**：易于添加新的新闻源

## 🧪 测试建议

```bash
# 1. 启动网络（如果尚未运行）
# 在另一个终端

# 2. 启动 news_assistant
python studio/my_first_network/agents/news_assistant.py

# 3. 测试提及
# 在网络中发送: @news-assistant
```

## 🔮 未来扩展

- [ ] 添加更多新闻源（Twitter, Medium 等）
- [ ] 支持自定义搜索关键词
- [ ] 添加新闻分类和过滤
- [ ] 实现多语言支持
- [ ] 添加新闻趋势分析

---

**核心理念**：按需服务、高效缓存、清晰架构 🚀
