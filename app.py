import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# 页面基础标题
st.title("✨ 设计图元器件解析器")

# 1. API 配置
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("密钥未配置，请检查 Streamlit Secrets。")
    st.stop()

# 2. 文件上传
uploaded_file = st.file_uploader("上传设计图 (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file is not None:
    # 预览图片 (PDF 不预览)
    if uploaded_file.type != "application/pdf":
        img = Image.open(uploaded_file)
        st.image(img, use_container_width=True)
    else:
        st.info("📂 PDF 文档已加载")

    # 3. 点击解析按钮
    if st.button("🚀 开始解析并导出 Excel"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "识别图中所有元器件。只输出CSV格式：元器件名称,数量。不要解释文字。"
        
        try:
            with st.spinner("AI 正在解析中..."):
                if uploaded_file.type == "application/pdf":
                    # PDF 专用格式
                    content = [prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                else:
                    # 图片格式
                    img = Image.open(uploaded_file)
                    content = [prompt, img]
                
                response = model.generate_content(content)
                
                # 提取并清理数据
                res_text = response.text.replace('```csv', '').replace('```', '').strip()
                df = pd.read_csv(io.StringIO(res_text), names=["名称", "数量"])
                
                # 展示结果
                st.subheader("📊 解析清单")
                st.table(df)

                # 生成 Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 下载 Excel 结果",
                    data=buffer.getvalue(),
                    file_name="result.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"发生错误: {e}")
