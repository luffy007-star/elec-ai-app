import streamlit as st
import google.generativeai as genai
import pandas as pd
import io

st.set_page_config(page_title="Gemini 3 解析器", layout="centered")

# 1. API 配置
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("密钥未配置，请在 Streamlit Secrets 中检查。")
    st.stop()

st.title("🚀 Gemini 3 设计图解析神器")

# 2. 自动检测模型 (优先 Gemini 3)
@st.cache_resource
def find_model():
    try:
        # 获取账号下所有可用模型
        available_models = [m.name for m in genai.list_models()]
        # 按照性能和新旧程度排序
        order = ['models/gemini-3-flash', 'models/gemini-1.5-flash', 'models/gemini-pro-vision']
        for m in order:
            if m in available_models: return m
        return available_models[0]
    except:
        return 'gemini-1.5-flash'

target_model = find_model()

# 3. 文件上传逻辑
uploaded_file = st.file_uploader("上传图纸 (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.info(f"📂 文件已就绪 | 调用的模型: {target_model}")
    
    if st.button("✨ 执行智能解析"):
        try:
            model = genai.GenerativeModel(target_model)
            prompt = "识别图中所有元器件。请仅输出CSV格式：名称,数量。不要解释文字。"
            
            with st.spinner("AI 正在解析中，请稍候..."):
                # 兼容 PDF 和图片的最新 Payload 格式
                blob = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
                response = model.generate_content([prompt, blob])
                
                if response.text:
                    # 数据清洗
                    clean_text = response.text.replace('```csv', '').replace('```', '').strip()
                    df = pd.read_csv(io.StringIO(clean_text), names=["名称", "数量"])
                    
                    st.subheader("📊 解析清单")
                    st.table(df)

                    # 生成 Excel
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    st.download_button("📥 下载 Excel 表格", buffer.getvalue(), "list.xlsx")
                else:
                    st.warning("AI 返回了空内容，请尝试换一张更清晰的图。")
        except Exception as e:
            st.error(f"解析出错: {str(e)}")
            st.info("提示：如果看到 404，请确认你的 API 项目是否已启用 Generative Language API。")
