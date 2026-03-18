import streamlit as st
import google.generativeai as genai
import pandas as pd
import io

st.set_page_config(page_title="元器件解析器", layout="centered")
st.title("✨ 设计图元器件解析器")

# 1. 初始化 API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("请在 Streamlit Secrets 中配置 GOOGLE_API_KEY")
    st.stop()

# 2. 动态寻找可用模型 (解决 404 的核心)
@st.cache_resource
def get_working_model():
    try:
        # 获取你账号下所有能用的模型名
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 优先级：3 Flash > 1.5 Flash > 1.5 Pro
        for pref in ['models/gemini-3-flash', 'models/gemini-1.5-flash', 'models/gemini-1.5-pro']:
            if pref in available: return pref
        return available[0] if available else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash"

active_model = get_working_model()

# 3. 上传界面
uploaded_file = st.file_uploader("上传图纸 (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.success(f"已连接引擎: {active_model}")
    
    if st.button("🚀 开始智能解析"):
        try:
            model = genai.GenerativeModel(active_model)
            prompt = "识别图中的所有元器件。直接输出 CSV：名称,数量。不要解释。"
            
            with st.spinner("AI 正在全力解析中..."):
                # 2026 最新多模态数据包格式
                doc_data = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
                response = model.generate_content([prompt, doc_data])
                
                # 清洗数据
                csv_data = response.text.replace('```csv', '').replace('```', '').strip()
                df = pd.read_csv(io.StringIO(csv_data), names=["元器件名称", "数量"])
                
                st.subheader("📊 解析清单")
                st.table(df)

                # Excel 导出
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 下载 Excel 表格", buf.getvalue(), "result.xlsx")
        except Exception as e:
            st.error(f"解析失败: {e}")
            st.info("如果还是 404，请确认你在 Google Cloud Console 启用了 'Generative Language API'")
