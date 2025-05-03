# backend/api_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient


load_dotenv()

# FastAPI 인스턴스
app = FastAPI()

# 입력 모델 정의
class MessageInput(BaseModel):
    messages: list


@app.post("/predict/agent")
async def predict(req: MessageInput):

    print(req)
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    llm = AzureChatOpenAI(
        azure_deployment="gpt-4o-mini",
        azure_endpoint="https://sb-azure-openai-studio.openai.azure.com/",
        api_version="2024-10-21",
        verbose=True,
        temperature=0  # 창의성 조정,
    )

    async with MultiServerMCPClient(
        {
            "math": {
                "url": "http://3.35.136.196:7004/sse",
                "transport": "sse"
            },
            "tavily-mcp": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "tavily-mcp@0.1.4"],
                "env": {
                    "TAVILY_API_KEY": tavily_api_key
                }
            }
        }
    ) as client:
        print(client.get_tools())
        agent = create_react_agent(llm, client.get_tools())
        response = await agent.ainvoke({"messages": req.messages})

        print(f'response = {response}')

        for m in response['messages']:
            m.pretty_print()

    return {"response": response['messages'][-1].content}


@app.post("/predict/langchain")
def predict(req: MessageInput):

    print(req)

    llm = AzureChatOpenAI(
        azure_deployment="gpt-4o-mini",
        azure_endpoint="https://sb-azure-openai-studio.openai.azure.com/",
        api_version="2024-10-21",
        temperature=0  # 창의성 조정,
    )
    response = llm.invoke(req.messages)

    return {"response": response.content}