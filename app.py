import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

st.set_page_config(page_title="设计图元器件解析器", layout="centered")

# API 配置
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("密钥未配置")
    st.stop()

st.markdown("<h2 style='text-align: center;'>✨ 设计图元器件解析器</h2>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("上传设计图 (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        st.info("📂 PDF 文档已就绪")
    else:
        st.image(Image.open(uploaded_file), use_container_width=True)

    if st.button("🚀 开始解析并导出 Excel"):
        # --- 核心修复：尝试多种可能的模型名称 ---
        model_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-pro']
        success = False
        
        with st.spinner("AI 正在扫描并分析..."):
            for name in model_names:
                try:
                    model = genai.GenerativeModel(name)
                    prompt = "识别图中的所有元器件。只输出CSV格式：元器件名称,数量。不要解释文字。"
                    
                    if uploaded_file.type == "application/pdf":
                        content = [prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                    else:
                        img = Image.open(uploaded_file)
                        content = [prompt, img]
                    
                    response = model.generate_content(content)
                    
                    # 如果能运行到这里，说明模型调用成功
                    res_text = response.text.replace('```csv', '').replace('```', '').strip()
                    df = pd.read_csv(io.StringIO(res_text), names=["元器件名称", "数量"])
                    
                    st.subheader("📊 解析结果")
                    st.table(df)

                    # 导出 Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    st.download_button("📥 下载 Excel 表格", output.getvalue(), "Result.xlsx")
                    success = True
                    break # 成功了就跳出循环
                except Exception:
                    continue # 失败了尝试下一个模型名称
            
            if not success:
                st.error("所有模型尝试均失败。请检查 API Key 是否已在 Google AI Studio 开启了 Gemini API 权限。")
