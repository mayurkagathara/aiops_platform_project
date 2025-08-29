# tools/vm_cpu_tool.py
from langchain.tools import tool
import requests
import statistics
import datetime

VM_URL = "http://localhost:8428/prometheus/api/v1"

@tool
def query_cpu(host: str, start: str, end: str, step: str = "5m") -> dict:
    """
    Query CPU usage for a given host from VictoriaMetrics and return statistics.
    
    Args:
        host: Hostname or ID.
        start: Start time (RFC3339).
        end: End time (RFC3339).
        step: Resolution step (default: 5m).
    
    Returns:
        Dict with CPU statistics and sample points.
    """
    query = f"nab_aws_cpu_value{{host='{host}'}}"
    url = f"{VM_URL}/query_range"
    params = {"query": query, "start": start, "end": end, "step": step, "limit": 100} 

    resp = requests.get(url, params=params, timeout=60)
    if resp.status_code != 200:
        return {"error": f"Query failed: {resp.text}"}

    data = resp.json().get("data", {}).get("result", [])
    if not data:
        return {"error": "No data found for given host/time range"}

    # Flatten values into list
    values = []
    timestamps = []
    for series in data:
        for ts, val in series["values"]:
            try:
                v = float(val)
                values.append(v)
                timestamps.append(datetime.datetime.utcfromtimestamp(float(ts)).isoformat())
            except:
                continue

    if not values:
        return {"error": "No valid numeric values found"}

    # Compute stats
    stats = {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "stdev": statistics.pstdev(values) if len(values) > 1 else 0,
        "first_point": {"time": timestamps[0], "value": values[0]},
        "last_point": {"time": timestamps[-1], "value": values[-1]},
    }

    return {
        "host": host,
        "start": start,
        "end": end,
        "step": step,
        "stats": stats,
        "sample_values": values,  # only first 10 values to avoid overload
    }


# aiops_agent.py
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
# from tools.vm_cpu_tool import query_cpu
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI # or from langchain_community.chat_models import ChatOpenAI

load_dotenv()

# model_name = "qwen2.5:1.5b"
# llm = ChatOllama(model="qwen2.5:1.5b")
#llm = ChatOllama(model=model_name, base_url="http://localhost:11434")
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    model_name="qwen/qwen3-235b-a22b:free", # Replace with your desired model
    openai_api_key=os.environ.get("OPENROUTER_API_KEY")
)
tools = [query_cpu]
# Create the agent
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt="You are an AIOps assistant that can call tools for data. Use tools when needed."
)

def investigate_cpu(host: str, start: str, end: str):
    # Build a clear user message and required schema so agent knows to call the tool
    user_prompt = (
        f"Investigate CPU for host={host} from {start} to {end}.\n"
        "You have access to a tool that returns CPU statistics for the requested range.\n"
        "Steps: (1) Use the tool to fetch CPU stats. (2) Summarize CPU Health with min/mean/max/stdev. "
        "(3) Give Possible Root Cause hypotheses and Troubleshooting steps.\n"
        "Return concise maximum 200 words final answer with headings: CPU Health, Possible Root Cause, Troubleshooting / Solution."
    )

    # IMPORTANT: pass messages key (correct input shape)
    response = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})

    # response is a dict with 'messages' list and optionally 'structured_response'
    # Inspect messages to find assistant final reply:
    # messages = response.get("messages", [])
    # The final assistant message is often the last message with role 'assistant'
    # assistant_texts = [m.get("content", "") for m in messages if m.get("role") == "assistant"]
    # final_text = assistant_texts[-1] if assistant_texts else ""

    # Optionally, inspect structured_response if present:
    # structured = response.get("structured_response")

    # return {"raw": response, "final_text": final_text, "structured": structured}
    return response

if __name__ == "__main__":
    out = investigate_cpu(
        host="ac20cd",
        start="2025-07-14T22:14:08Z",
        end="2025-07-15T03:43:58Z"
    )
    print(out['messages'][-1].content)
    # print("=== Final assistant text ===\n", out["final_text"])
    # print("\n=== Raw response keys ===\n", out["raw"].keys())
    # if out["structured"]:
    #     print("\n=== Structured response ===\n", out["structured"])