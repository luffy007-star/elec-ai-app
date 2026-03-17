import streamlit as st
import google.generativeai as genai
import pandas as pd
import io

# 页面基础装修
st.set_page_config(page_title="AI 设计图解析", layout="centered")
st.title("🚀 设计图元器件解析器")

# API 安全配置
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("密钥未配置，请检查 Secrets。")
    st.stop()

# 核心：自动寻找当前最可用的最新模型
@st.cache_resource
def get_latest_model():
    try:
        # 获取账号下所有模型
        all_models = [m.name for m in genai.list_models()]
        # 按照 3 -> 1.5 的优先级排序
        for preferred in ['models/gemini-3-flash', 'models/gemini-1.5-flash']:
            if preferred in all_models:
                return preferred
        return 'gemini-1.5-flash' # 保底
    except:
        return 'gemini-1.5-flash'

model_to_use = get_latest_model()

# 文件上传
uploaded_file = st.file_uploader("上传图纸 (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.success(f"📂 已加载: {uploaded_file.name} | 引擎: {model_to_use}")
    
    if st.button("✨ 开始智能解析"):
        try:
            model = genai.GenerativeModel(model_to_use)
            prompt = "你是一个电子工程师，请识别图中的所有元器件。直接输出 CSV：名称,数量。不要解释。"
            
            with st.spinner("AI 正在深度扫描分析..."):
                # 统一打包文件数据
                doc_blob = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
                response = model.generate_content([prompt, doc_blob])
                
                # 数据处理逻辑
                res_text = response.text.replace('```csv', '').replace('```', '').strip()
                df = pd.read_csv(io.StringIO(res_text), names=["名称", "数量"])
                
                st.subheader("📊 提取到的清单")
                st.table(df)

                # Excel 导出
                excel_io = io.BytesIO()
                with pd.ExcelWriter(excel_io, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button("📥 下载 Excel 表格", excel_io.getvalue(), "list.xlsx")
        except Exception as e:
            st.error(f"解析中止: {str(e)}")
            st.info("提示：若报错 404，请确认你的 Google Cloud 项目已启用 Generative Language API。")
