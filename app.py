import streamlit as st
import google.generativeai as genai

# 1. 尝试从后台读取 API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ 还没配置 API Key 呢！请在 Streamlit 后台设置。")
    st.stop()

# 2. 注入你在 Google AI Studio 调教好的灵魂
st.title("✨ 我的专属 AI 助手")
system_prompt = "我希望做一个可以解析设计图的页面，当我把设计图传进去的时候，可以解析这个设计图有哪些元器件和对应的数量" # 替换成你在 AI Studio 里的 System Instruction

# 3. 初始化模型
model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_prompt)

# 4. 简易聊天界面逻辑
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    response = model.generate_content(prompt)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    st.chat_message("assistant").write(response.text)
