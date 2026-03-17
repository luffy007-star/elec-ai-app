import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# 页面基础配置
st.set_page_config(page_title="设计图元器件解析器", layout="centered")

# CSS 样式
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #059669; color: white; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>✨ 设计图元器件解析器</h2>", unsafe_allow_html=True)

# API 配置
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("请在 Secrets 中配置 API Key")
    st.stop()

uploaded_file = st.file_uploader("上传设计图 (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

if uploaded_file is not None:
    if uploaded_file.type != "application/pdf":
        image = Image.open(uploaded_file)
        st.image(image, caption="已加载图片", use_container_width=True)
    else:
        st.info("📂 已加载 PDF 文档，准备解析...")

    if st.button("🚀 开始智能解析"):
        # 换回标准模型名称
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """
            你是一个专业的设计图解析专家。请识别图中的所有元器件。
            仅输出 CSV 格式数据，包含两列：元器件名称, 数量。
            不要任何开场白。
            示例：
            电阻, 10
            电容, 5
            """
            
            with st.spinner("🤖 AI 正在处理中..."):
                if uploaded_file.type == "application/pdf":
                    content = [prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                else:
                    image = Image.open(uploaded_file)
                    content = [prompt, image]
                
                response = model.generate_content(content)
                
                # 处理返回结果
                res_text = response.text.replace('```csv', '').replace('```', '').strip()
                df = pd.read_csv(io.StringIO(res_text), names=["元器件名称", "数量"])
                
                st.markdown("### 📊 解析结果")
                st.table(df)

                # Excel 导出
                excel_io = io.BytesIO()
                with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button("📥 下载 Excel 表格", excel_io.getvalue(), "解析结果.xlsx")
        except Exception as e:
            # 这里的报错会告诉你更详细的信息
            st.error(f"解析出错：{str(e)}")
            st.info("提示：如果依然报 404，可能是 API Key 所在项目未激活 Gemini API 权限。")
else:
    st.info("💡 请上传图纸开始工作")
