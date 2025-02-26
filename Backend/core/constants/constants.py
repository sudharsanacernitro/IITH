from openai import OpenAI

ollama_client = OpenAI(
    base_url=f"http://localhost:11434/v1",
    api_key="ollama"
)

http_proxy = 'socks5://127.0.0.1:9050'

https_proxy = 'socks5://127.0.0.1:9050'

ip = "localhost"

Database_URI="mongodb://localhost:27017"  
DB_NAME="AI-assistant"
Collections={
    'login':'login',
    'signup':'login',
    'storeQueries':'Queries'
}

