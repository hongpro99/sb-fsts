# frontend/app_llm_chat.py
import streamlit as st
import requests

# 🔄 상태 저장
if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.title("💬 LLM Frontend Chat")

# 기존 채팅 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 입력
if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    print(f'prompt = {prompt}')
    with st.chat_message("user"):
        st.markdown(prompt)

    # 💬 Backend API 호출
    backend_url = "http://3.35.136.196:7002/predict/agent"  # 배포 시 IP 변경
    response = requests.post(backend_url, json={"messages": st.session_state.messages})
    assistant_reply = response.json()["response"]

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)