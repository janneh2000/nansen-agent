# NansenAgent 🧠⛓️

> AI-powered Onchain Intelligence — ask blockchain questions in plain English.

Built with **Nansen CLI** + **Claude AI** for the Nansen Mac Mini Challenge.

## What it does

NansenAgent lets anyone interrogate onchain data without knowing CLI syntax.
You ask a question → Claude figures out which Nansen commands to run → runs them → gives you a clean analysis.

**Example:**
```
You: "What tokens are smart money buying on Solana right now?"

NansenAgent:
  → nansen research smart-money netflow --chain solana --timeframe 24h --limit 10
  → nansen research token screener --chain solana --smart-money --sort net_flow_usd:desc
  
  Analysis: Smart money is accumulating $BONK and $JUP with +$2.3M 
  netflow in 24h. Top wallets reduced $WIF exposure by 18%...
```

## Setup

```bash
# 1. Install Nansen CLI
npm install -g nansen-cli
nansen login   # or: export NANSEN_API_KEY=your_key

# 2. Install Python deps
pip install -r requirements.txt

# 3. Set Anthropic API key
export ANTHROPIC_API_KEY=your_anthropic_key

# 4. Run the agent
python server.py

# 5. Open http://localhost:5000
```

## Stack

- **Nansen CLI** — onchain data across 18+ chains
- **Claude API (Sonnet)** — NLP → command parsing + analysis
- **Flask** — lightweight HTTP server
- **Pure HTML/CSS/JS** — zero-dependency beautiful UI

## Features

- 🔍 Natural language → Nansen CLI commands
- 📊 Real-time command execution + results
- 🎨 Beautiful dark terminal UI
- ⚡ Multi-command orchestration per query
- 📋 Raw JSON data panel for power users
- 🔢 API call counter for hackathon eligibility

## Supported Query Types

- Smart money flows by chain/timeframe
- Token screening and trending analysis
- Wallet profiling and portfolio analysis
- Smart money top traders
- Cross-chain comparison

## License

MIT — Built for #NansenCLI hackathon
