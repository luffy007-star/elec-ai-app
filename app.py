import streamlit as st
import google.generativeai as genai
import pandas as pd
import io

# 1. 页面配置
st.set_page_config(page_title="Gemini 3 设计图解析", layout="centered")

# 2. 配置 API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("请先在 Secrets 中配置 API Key")
    st.stop()

st.title("🚀 Gemini 3 元器件解析器")

# 3. 获取最新的模型列表（自动识别 Gemini 3）
@st.cache_resource
def get_model():
    # 优先寻找 gemini-3-flash
    return "gemini-3-flash"

current_model = get_model()

# 4. 文件上传
uploaded_file = st.file_uploader("上传 PDF 或图片", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.success(f"已连接到 {current_model}")
    
    if st.button("✨ 执行 AI 深度解析"):
        try:
            # 初始化 Gemini 3 模型
            model = genai.GenerativeModel(current_model)
            
            # 针对设计图的专业指令
            prompt = """
            作为高级电子工程师，请分析此文件并提取元器件清单。
            请直接输出 CSV 格式：名称,数量
            不要输出任何多余的文字。
            """
            
            with st.spinner("Gemini 3 正在高速处理中..."):
                # 构造符合最新规范的多模态输入
                content_payload = {
                    "mime_type": uploaded_file.type,
                    "data": uploaded_file.getvalue()
                }
                
                response = model.generate_content([prompt, content_payload])
                
                # 数据清洗与展示
                raw_data = response.text.replace('```csv', '').replace('```', '').strip()
                df = pd.read_csv(io.StringIO(raw_data), names=["元器件名称", "数量"])
                
                st.subheader("📊 识别结果")
                st.table(df)

                # Excel 导出逻辑
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button("📥 导出 Excel", output.getvalue(), "清单.xlsx")
                
        except Exception as e:
            st.error(f"调用 Gemini 3 失败: {str(e)}")
