#!/usr/bin/env python3
"""
NansenAgent - AI-powered Onchain Intelligence Agent
Uses Nansen CLI + Claude API to answer blockchain questions in natural language
"""

import subprocess
import json
import os
import anthropic
from typing import Optional

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are NansenAgent, an expert onchain intelligence AI assistant.
You help users understand blockchain data by translating their questions into Nansen CLI commands and analyzing the results.

The Nansen CLI syntax is:
- nansen research smart-money netflow [--chain CHAIN] [--timeframe TIMEFRAME] [--limit N]
- nansen research smart-money transfers [--chain CHAIN] [--timeframe TIMEFRAME]
- nansen research smart-money top-traders [--chain CHAIN] [--timeframe TIMEFRAME] [--limit N]
- nansen research token screener [--chain CHAIN] [--timeframe TIMEFRAME] [--sort FIELD:dir]
- nansen research token holders --token ADDRESS [--chain CHAIN] [--limit N]
- nansen research profiler --address ADDRESS [--chain CHAIN]
- nansen research portfolio --address ADDRESS [--chain CHAIN]
- nansen research search --query TEXT

Common chains: ethereum, solana, base, bnb, arbitrum, polygon, optimism, avalanche
Common timeframes: 5m, 1h, 6h, 24h, 7d, 30d

When a user asks a question:
1. Determine which nansen commands are needed (1-4 commands)
2. Return a JSON object with this exact structure:
{
  "commands": ["nansen research smart-money netflow --chain ethereum --timeframe 24h --limit 10", ...],
  "analysis_prompt": "A brief description of what you're looking for"
}

Only return valid JSON, nothing else."""

ANALYSIS_PROMPT = """You are NansenAgent, an expert crypto analyst. 
You have just run Nansen CLI commands and received blockchain data.
Analyze the data and provide a clear, insightful summary.
Be specific about numbers, tokens, and trends you observe.
Format your response with clear sections using markdown-style headers (##).
Keep it focused and actionable — highlight what matters for traders/investors.
End with a brief "Key Takeaway" section."""


def run_nansen_command(command: str) -> dict:
    """Execute a nansen CLI command and return parsed JSON output."""
    try:
        cmd_parts = command.strip().split()
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip()
        
        try:
            return {"success": True, "data": json.loads(output), "command": command}
        except json.JSONDecodeError:
            return {"success": True, "data": output, "command": command}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "command": command}
    except FileNotFoundError:
        return {"success": False, "error": "nansen-cli not found. Run: npm install -g nansen-cli", "command": command}
    except Exception as e:
        return {"success": False, "error": str(e), "command": command}


def parse_commands(user_question: str) -> dict:
    """Use Claude to determine which nansen commands to run."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_question}]
    )
    
    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    return json.loads(text)


def analyze_results(question: str, results: list) -> str:
    """Use Claude to analyze nansen CLI results."""
    results_text = ""
    for r in results:
        results_text += f"\n\nCommand: {r['command']}\n"
        if r["success"]:
            data = r["data"]
            if isinstance(data, dict):
                results_text += json.dumps(data, indent=2)[:3000]
            else:
                results_text += str(data)[:3000]
        else:
            results_text += f"Error: {r['error']}"
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=ANALYSIS_PROMPT,
        messages=[{
            "role": "user",
            "content": f"User question: {question}\n\nNansen CLI Results:{results_text}"
        }]
    )
    
    return response.content[0].text


def process_query(question: str) -> dict:
    """Main pipeline: question → commands → execution → analysis."""
    try:
        # Step 1: Parse question into commands
        parsed = parse_commands(question)
        commands = parsed.get("commands", [])
        
        if not commands:
            return {
                "success": False,
                "error": "Could not determine what to search for. Try asking about smart money, tokens, or wallet analysis.",
                "commands": [],
                "results": [],
                "analysis": ""
            }
        
        # Step 2: Execute commands
        results = []
        for cmd in commands[:4]:  # max 4 commands per query
            result = run_nansen_command(cmd)
            results.append(result)
        
        # Step 3: Analyze results
        analysis = analyze_results(question, results)
        
        return {
            "success": True,
            "commands": commands,
            "results": results,
            "analysis": analysis
        }
        
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse command structure. Please rephrase your question.",
            "commands": [],
            "results": [],
            "analysis": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "commands": [],
            "results": [],
            "analysis": ""
        }


if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What tokens are smart money buying on Ethereum?"
    print(f"\n🔍 Question: {question}\n")
    result = process_query(question)
    print(json.dumps(result, indent=2))
