# backend/api_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import os
from langchain_openai import AzureChatOpenAI


# FastAPI 인스턴스
app = FastAPI()

# 입력 모델 정의
class MessageInput(BaseModel):
    messages: list

@app.post("/predict")
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