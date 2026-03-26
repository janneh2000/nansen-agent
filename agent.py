#!/usr/bin/env python3
import subprocess
import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are NansenAgent, an expert onchain intelligence AI assistant.
Translate user questions into Nansen CLI commands and analyze results.

Valid Nansen CLI commands ONLY:
- nansen research smart-money netflow [--chain CHAIN] [--timeframe TIMEFRAME] [--limit N]
- nansen research smart-money transfers [--chain CHAIN] [--timeframe TIMEFRAME] [--limit N]
- nansen research smart-money dex-trades [--chain CHAIN] [--timeframe TIMEFRAME] [--limit N]
- nansen research smart-money holdings [--chain CHAIN] [--limit N]
- nansen research smart-money dcas [--chain CHAIN] [--timeframe TIMEFRAME] [--limit N]
- nansen research token screener [--chain CHAIN] [--timeframe TIMEFRAME] [--sort FIELD:dir] [--limit N]
- nansen research profiler --address ADDRESS [--chain CHAIN]
- nansen research portfolio --address ADDRESS [--chain CHAIN]

NEVER use: top-traders, token holders without --token flag.

Chains: ethereum, solana, base, bnb, arbitrum, polygon, optimism, avalanche
Timeframes: 5m, 1h, 6h, 24h, 7d, 30d

Return ONLY valid JSON, nothing else:
{"commands": ["nansen research smart-money netflow --chain solana --timeframe 24h --limit 10"], "analysis_prompt": "description"}"""

ANALYSIS_PROMPT = """You are NansenAgent, an expert crypto analyst.
Analyze the Nansen CLI data and provide clear, insightful commentary.
Use ## for section headers. Bold important numbers with **value**.
End with a ## Key Takeaway section.
If data shows errors, explain what the data limitation means and what you can still infer."""


# 🔥 FIXED: safer subprocess (no hanging)
def run_nansen_command(command: str) -> dict:
    try:
        result = subprocess.run(
            command.strip().split(),
            capture_output=True,
            text=True,
            timeout=20,
            env=os.environ.copy()
        )

        output = result.stdout.strip() or result.stderr.strip()

        if not output:
            return {"success": False, "error": "No output", "command": command}

        try:
            return {"success": True, "data": json.loads(output), "command": command}
        except json.JSONDecodeError:
            return {"success": True, "data": output, "command": command}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "command": command}
    except Exception as e:
        return {"success": False, "error": str(e), "command": command}


# 🔥 FIXED: more robust parsing
def parse_commands(user_question: str) -> dict:
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_question}]
        )

        text = response.content[0].text.strip()

        # Clean markdown if Claude adds it
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                try:
                    return json.loads(part)
                except:
                    continue

        return json.loads(text)

    except Exception as e:
        return {"commands": [], "error": f"Parse error: {str(e)}"}


# 🔥 FIXED: limit payload + safe analysis
def analyze_results(question: str, results: list) -> str:
    try:
        results_text = ""

        for r in results:
            results_text += f"\n\nCommand: {r['command']}\n"

            if r["success"]:
                data = r["data"]
                if isinstance(data, (dict, list)):
                    results_text += json.dumps(data, indent=2)[:2000]
                else:
                    results_text += str(data)[:2000]
            else:
                results_text += f"Error: {r['error']}"

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=ANALYSIS_PROMPT,
            messages=[{
                "role": "user",
                "content": f"User question: {question}\n\nNansen CLI Results:{results_text}"
            }]
        )

        return response.content[0].text

    except Exception as e:
        return f"## Analysis Error\nCould not analyze results: {str(e)}"


# 🔥 FIXED: overall stability
def process_query(question: str) -> dict:
    try:
        print("🔍 Parsing commands...")
        parsed = parse_commands(question)

        commands = parsed.get("commands", [])
        print(f"⚙️ Commands: {commands}")

        if not commands:
            return {
                "success": False,
                "error": "Could not determine what to search for.",
                "commands": [],
                "results": [],
                "analysis": ""
            }

        results = []

        print("🚀 Running commands...")
        for cmd in commands[:3]:  # limit to 3 (faster + safer)
            result = run_nansen_command(cmd)
            results.append(result)

        print("🧠 Analyzing results...")
        analysis = analyze_results(question, results)

        print("✅ Done")

        return {
            "success": True,
            "commands": commands,
            "results": results,
            "analysis": analysis
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Agent error: {str(e)}",
            "commands": [],
            "results": [],
            "analysis": ""
        }


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What tokens are smart money buying on Solana?"
    print(json.dumps(process_query(q), indent=2))