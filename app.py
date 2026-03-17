import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# 1. 页面配置
st.set_page_config(page_title="设计图元器件解析器", layout="centered")

# 2. 注入 CSS 视觉装修
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stApp { max-width: 850px; margin: 0 auto; }
    .stButton>button { 
        width: 100%; border-radius: 8px; background-color: #059669; 
        color: white; height: 3.5em; font-weight: bold; border: none;
    }
    .upload-hint { 
        padding: 50px; border: 2px dashed #d1d5db; border-radius: 15px; 
        text-align: center; background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>✨ 设计图元器件解析器</h2>", unsafe_allow_html=True)

# 3. 配置 API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ 还没配置 API Key 呢！请在 Streamlit 后台 Secrets 设置。")
    st.stop()

# 4. 文件上传
uploaded_file = st.file_uploader("上传设计图 (PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

if uploaded_file is not None:
    if uploaded_file.type != "application/pdf":
        image = Image.open(uploaded_file)
        st.image(image, caption="待解析的设计图", use_container_width=True)
    else:
        st.info("📂 已加载 PDF 文档，准备进行智能扫描...")

    if st.button("🚀 开始智能解析"):
        # 使用兼容性更好的模型全称
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = """
        你是一个精通设计图纸的专家。请识别图中的所有元器件。
        要求：
        1. 仅输出 CSV 格式数据：元器件名称, 数量。
        2. 不要输出任何开场白、结尾或 Markdown 标签。
        示例：
        电阻, 10
        电容, 5
        """
        
        with st.spinner("🤖 AI 正在深度解析中，请稍候..."):
            try:
                # 针对不同格式打包数据
                if uploaded_file.type == "application/pdf":
                    content = [prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                else:
                    content = [prompt, image]
                
                response = model.generate_content(content)
                
                # 清洗数据并转换
                clean_text = response.text.replace('```csv', '').replace('```', '').strip()
                df = pd.read_csv(io.StringIO(clean_text), names=["元器件名称", "数量"])
                
                st.markdown("### 📊 解析结果清单")
                st.table(df)

                # 生成 Excel 下载流
                excel_data = io.BytesIO()
                with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='解析清单')
                
                st.download_button(
                    label="📥 下载 Excel 结果表格",
                    data=excel_data.getvalue(),
                    file_name="元器件解析结果.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"解析过程中出现小状况：{str(e)}")
else:
    st.markdown("""
        <div class="upload-hint">
            <p style="font-size: 50px;">📄</p>
            <h4>等待解析</h4>
            <p>上传您的设计图并点击按钮，AI 将为您提取清单并生成 Excel。</p>
        </div>
    """, unsafe_allow_html=True)
