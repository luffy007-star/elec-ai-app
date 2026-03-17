import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# 页面配置
st.set_page_config(page_title="设计图元器件解析器", layout="centered")

# 注入 CSS
st.markdown("""
<style>
.main { background-color: #f8f9fa; }
.stApp { max-width: 850px; margin: 0 auto; }
.stButton>button { width: 100%; border-radius: 8px; background-color: #059669; color: white; height: 3.5em; font-weight: bold; border: none; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>✨ 设计图元器件解析器</h2>", unsafe_allow_html=True)

# 配置 API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ 还没配置 API Key 呢！请在 Streamlit 后台 Secrets 设置。")
    st.stop()

uploaded_file = st.file_uploader("上传设计图 (支持 PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

if uploaded_file is not None:
    if uploaded_file.type != "application/pdf":
        image = Image.open(uploaded_file)
        st.image(image, caption="待解析的设计图", use_container_width=True)
    else:
        st.info("📂 已加载 PDF 文档，准备解析...")

    if st.button("🚀 开始智能解析"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "识别图中所有元器件。只输出CSV格式：元器件名称,数量。不要解释，不要Markdown标签。"
        
        with st.spinner("🤖 AI 正在解析中..."):
            try:
                if uploaded_file.type == "application/pdf":
                    content = [prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                else:
                    content = [prompt, image]
                
                response = model.generate_content(content)
                clean_text = response.text.replace('```csv', '').replace('```', '').strip()
                
                df = pd.read_csv(io.StringIO(clean_text), names=["元器件名称", "数量"])
                st.markdown("### 📊 解析结果清单")
                st.table(df)

                excel_data = io.BytesIO()
                with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button(label="📥 下载 Excel 结果表格", data=excel_data.getvalue(), file_name="元器件解析结果.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(f"解析出错：{str(e)}")
else:
    st.info("💡 请先上传文件，然后点击解析按钮。")
