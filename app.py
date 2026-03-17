
    import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io
import re

st.set_page_config(page_title="设计图元器件解析器", layout="centered")

# 1. 配置 API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("请在 Secrets 中配置 API Key")
    st.stop()

st.markdown("<h2 style='text-align: center;'>✨ 设计图元器件解析器</h2>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("上传设计图 (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file:
    if uploaded_file.type != "application/pdf":
        image = Image.open(uploaded_file)
        st.image(image, use_container_width=True)
    else:
        st.info("已加载 PDF 文档，准备解析...")

    if st.button("🚀 开始智能解析"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "识别图中所有元器件。只输出CSV格式：元器件名称,数量。不要解释。"
        
        with st.spinner("AI 解析中..."):
            if uploaded_file.type == "application/pdf":
                content = [{"mime_type": "application/pdf", "data": uploaded_file.getvalue()}, prompt]
            else:
                content = [image, prompt]
            
            response = model.generate_content(content)
            
            # 清理 AI 返回的数据，只保留 CSV 部分
            clean_text = response.text.replace('```csv', '').replace('```', '').strip()
            
            try:
                df = pd.read_csv(io.StringIO(clean_text), names=["元器件名称", "数量"])
                st.table(df)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button("📥 下载 Excel 表格", output.getvalue(), "元器件清单.xlsx")
            except:
                st.error("解析失败，AI 返回内容无法识别。请尝试上传更清晰的图。")
                st.write(response.text)
