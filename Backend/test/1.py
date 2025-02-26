
import json
from swarm.repl import run_demo_loop
from swarm import Agent
from openai import OpenAI
from swarm import Swarm

import subprocess

# LLM and environment setup
ollama_client = OpenAI(
    base_url="http://localhost:11434/v1",        
    api_key="ollama"            
)

from dotenv import load_dotenv
import os

load_dotenv()
model = os.getenv('LLM_MODEL', 'qwen2.5-coder:3b')

# Function definitions
def run_nmap(target: str):
    """Scans a network with Nmap. Returns a summary of open ports."""
    command = f"nmap -sS -p- {target}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
    return result

def get_weather(location, time="now"):
    """Get the current weather in a given location. Location MUST be a city."""
    return json.dumps({"location": location, "temperature": "65", "time": time})

def send_email(recipient, subject, body):
    print("Sending email...")
    print(f"To: {recipient}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    return "Sent!"

# Define the agent
weather_agent = Agent(
    name="Weather Agent",
    instructions="You are a helpful cyber-security agent. Analyze tool outputs and provide concise summaries.",
    functions=[get_weather, send_email, run_nmap],
    model=model
)

# Define the swarm client
client = Swarm(client=ollama_client)

# Step 1: Execute Nmap and capture raw output
target_ip = "127.0.0.1"
nmap_output = run_nmap(target_ip)

# Step 2: Use LLM to summarize Nmap output
messages = [
    {"role": "system", "content": "You are a helpful cybersecurity agent. Summarize tool outputs."},
    {"role": "user", "content": f"The following is the output of an Nmap scan for target {target_ip}:\n{nmap_output}\nSummarize the key findings."}
]

response = client.run(
    agent=weather_agent,
    messages=messages,  # Pass updated messages
    context_variables={},
    stream=False,
    debug=False,
)

print(response)
