# EruSpace Network

A multi-agent network featuring AI assistants, news aggregation, and interactive dialogue agents.

## 📋 Overview

**EruSpace** is a production-ready OpenAgents network with:
- ✅ **Multi-channel support** (Home, News-board, EASTER-EGG)
- ✅ **Studio frontend** served at `/studio`
- ✅ **MCP protocol** enabled at `/mcp`
- ✅ **Docker-ready** with automated agent startup
- ✅ **Cloud deployment** optimized (Zeabur, Railway, Render)

## 🤖 Agents

| Agent | Type | Channel | Description |
|-------|------|---------|-------------|
| **Eru** | Python (LLM) | #Home | Helpful AI assistant using HuggingFace models |
| **Eru-news** | Python (LLM) | #News-board | News aggregator with ntfy integration |
| **Eru-alter 😈** | YAML (LLM) | #News-board | Witty news commentator (Kimi-k2-thinking) |
| **stuff 🤠** | Python/YAML (LLM) | #EASTER-EGG | AI writing consultant demo |
| **client** | YAML (LLM) | #EASTER-EGG | Interactive writer persona (demo) |

## 🏗️ Architecture

```
my_first_network/
├── network.yaml              # Network configuration
├── .env.example              # Environment variables template
├── agents/                   # Agent implementations
│   ├── eru.py               # Main assistant (Python)
│   ├── news_assistant_ntfy.py # News agent (Python)
│   ├── commentator.yaml     # News commentator (YAML)
│   ├── stuff.py/.yaml       # Writing consultant (hybrid)
│   └── client.yaml          # Demo writer persona
├── tools/                    # Shared tools
│   ├── ntfy_listener.py     # ntfy push notification listener
│   └── news_search.py       # Brave Search integration
└── docs/                     # Documentation
    ├── NEWS_ASSISTANT_README.md
    └── ENV_CONFIG_GUIDE.md
```

## 🚀 Quick Start

### Local Development

**1. Configure Environment Variables**

```bash
# Copy the template
cp .env.example .env

# Edit with your API keys
nano .env
```

Required keys:
```bash
HUGGINGFACE_API_KEY=hf_xxxxx  # For Eru agent
DASHSCOPE_API_KEY=sk-xxxxx    # For commentator/stuff agents
```

**2. Start the Network**

```bash
openagents network start src/openagents/my_first_network/network.yaml
```

**3. Launch Agents**

```bash
# Python agents
python src/openagents/my_first_network/agents/eru.py
python src/openagents/my_first_network/agents/news_assistant_ntfy.py

# YAML agents
openagents agent start src/openagents/my_first_network/agents/commentator.yaml
```

**4. Access Studio**

Open http://localhost:8700/studio/ in your browser.

### Docker Deployment

**Build and Run**

```bash
# Build image
docker build -t openagents-eruspace .

# Run with environment variables
docker run \
  -e HUGGINGFACE_API_KEY=hf_xxxxx \
  -e DASHSCOPE_API_KEY=sk-xxxxx \
  -p 8700:8700 -p 8600:8600 \
  openagents-eruspace
```

All agents and tools start automatically!

### Cloud Deployment (Zeabur/Railway)

**1. Push to GitHub**

```bash
git add .
git commit -m "Deploy EruSpace network"
git push origin main
```

**2. Configure Environment Variables in Platform**

Add these in your cloud platform's settings:
```
HUGGINGFACE_API_KEY=hf_xxxxx
DASHSCOPE_API_KEY=sk-xxxxx
GROQ_API_KEY=gsk_xxxxx  # Optional: for faster inference
```

**3. Deploy**

The platform will auto-build and deploy. Studio will be available at:
```
https://your-app.zeabur.app/studio/
```

## 🎮 Channel Guide

### #Home
- **Purpose**: General AI assistance
- **Agents**: Eru (responds to all messages)
- **Use Case**: Ask questions, get help, chat with AI

### #News-board
- **Purpose**: AI/tech news aggregation and commentary
- **Agents**: 
  - Eru-news (fetches and posts news)
  - Eru-alter 😈 (provides witty commentary)
- **Use Case**: Stay updated with curated news

### #EASTER-EGG
- **Purpose**: Interactive writing consultant demo
- **Agents**: 
  - stuff 🤠 (AI writing solution consultant)
  - client (aspiring web novel writer persona)
- **Use Case**: Demo of agent-to-agent dialogue

## 🔧 Configuration

### Network Settings

- **Network Name**: EruSpace
- **Node ID**: cqy-eru-1
- **HTTP Port**: 8700 (API + Studio + MCP)
- **gRPC Port**: 8600
- **Studio**: http://localhost:8700/studio/
- **MCP**: http://localhost:8700/mcp

### Channels

| Channel | Description | Default Agents |
|---------|-------------|----------------|
| Home | General assistance | Eru |
| News-board | News & commentary | Eru-news, Eru-alter |
| EASTER-EGG | Agent dialogue demo | stuff, client |

### Mods

- `openagents.mods.workspace.messaging` - Channel messaging
- `openagents.mods.core.shared_cache` - Shared data storage

## 🛠️ Tools

### ntfy_listener.py

Listens to ntfy push notifications and stores news for the news assistant agent.

**Features**:
- Real-time push notification listening
- Shared storage for agent access
- Automatic news deduplication

### news_search.py

Brave Search integration for news gathering.

**Usage**:
```python
from tools.news_search import BraveSearchClient

client = BraveSearchClient.from_env()
results = client.search("AI news", count=5, freshness="day")
```

## 📚 Documentation

- **[Environment Configuration Guide](ENV_CONFIG_GUIDE.md)** - Local dev vs cloud deployment
- **[News Assistant README](NEWS_ASSISTANT_README.md)** - Detailed news agent documentation
- **[Channel Filtering Guide](../../docs/tutorials/yaml-based-agents.mdx)** - Restrict agents to specific channels

## 🔐 Security

**⚠️ Never commit `.env` files to Git!**

- ✅ Use `.env.example` as template
- ✅ Configure API keys in cloud platform's environment variables
- ✅ Docker images don't include hardcoded keys
- ✅ All agents support both .env files and system environment variables

## 🐛 Troubleshooting

### Agent won't start in Docker

**Symptom**: eru.py starts locally but not in container

**Solution**: Check environment variables are set in cloud platform, not relying on .env file.

### Request timeout in cloud

**Symptom**: `Error during model interaction: Request timed out`

**Solution**: 
1. Add `request_timeout=120` to AgentConfig
2. Use Groq instead of HuggingFace for faster inference
3. Set `ENVIRONMENT=production` and configure fallback providers

### Agent responds in wrong channel

**Symptom**: Agent replies in all channels despite configuration

**Solution**: Use code-level channel filtering in `on_channel_post()`:
```python
async def on_channel_post(self, msg: ChannelMessageContext):
    if msg.channel != "Home":
        return  # Only respond in Home channel
    await self.run_agent(context=msg, instruction="...")
```

## 📖 Next Steps

1. **Customize Agents**: Edit instructions in `agents/*.yaml` files
2. **Add Channels**: Update `network.yaml` default_channels
3. **Create Tools**: Add shared utilities in `tools/` directory
4. **Deploy to Production**: Follow cloud deployment guide
5. **Explore Demos**: Check `demos/` folder for advanced patterns

## 🌐 Resources

- **Documentation**: https://openagents.org/docs/
- **Examples**: `../../demos/`
- **Community**: https://github.com/openagents-org/openagents
- **API Reference**: https://openagents.org/docs/api/

---

**Network Status**: Production-ready ✅  
**Studio**: Enabled at `/studio` ✅  
**MCP**: Enabled at `/mcp` ✅  
**Docker**: Auto-start configured ✅
