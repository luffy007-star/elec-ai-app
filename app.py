import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import re

# 1. 页面基本配置
st.set_page_config(page_title="电气设计图智能解析器", layout="wide")
st.markdown("<h1 style='text-align: center;'>⚡ 电气成套 B.O.M. 智能解析系统</h1>", unsafe_allow_html=True)

# 2. 安全读取 API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("❌ 未在 Secrets 中发现 API Key，请检查配置。")
    st.stop()

# 3. 动态识别最新模型 (优先调用 2.5 Flash)
@st.cache_resource
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['models/gemini-2.5-flash', 'models/gemini-1.5-flash']:
            if target in models: return target
        return models[0]
    except:
        return 'gemini-1.5-flash'

active_model = get_best_model()

# 4. 上传组件
st.info(f"当前解析引擎: {active_model}")
uploaded_file = st.file_uploader("请上传罗湖地铁或相关电气设计图纸 (支持 PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    # 5. 核心解析按钮
    if st.button("🚀 开始深度工程解析", use_container_width=True):
        try:
            model = genai.GenerativeModel(active_model)
            
            # --- 工程级高精度 Prompt ---
            prompt = """
            你是一个资深的电气设计工程师。请深度分析此文件，并提取出一份完整的成套设备物料清单 (BOM)。
            
            要求如下：
            1. **分柜识别**：必须识别出图纸中每一个独立的柜体（如：AH1进线柜、PT柜、电容柜等）。
            2. **参数提取**：必须包含元器件的完整规格型号（例如：3P 1250A, 100/5A, 40kvar等）。
            3. **输出格式**：仅输出严格的 CSV 格式，包含以下四列：柜子名称,元器件名称,规格型号,数量。
            4. **禁忌事项**：不要输出Markdown标签(如 ```csv)、不要解释性文字、不要空行。
            
            输出示例：
            柜子名称,元器件名称,规格型号,数量
            AH1进线柜,框架断路器,MT12H1 3P 1250A,1
            AH2电容柜,自愈式电容器,BSMJ0.45-20-3,10
            """

            with st.spinner("AI 正在扫描柜体结构并提取规格型号..."):
                # 构造多模态 Payload
                doc_part = {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
                response = model.generate_content([prompt, doc_part])
                
                # 数据深度清洗
                raw_text = response.text
                # 移除可能存在的 Markdown 符号
                clean_csv = re.sub(r'```[a-zA-Z]*\n?', '', raw_text).strip()
                
                # 将 CSV 转为 DataFrame
                df = pd.read_csv(io.StringIO(clean_csv), sep=',')
                
                # 统一列名（防止 AI 输出的表头微差）
                df.columns = ["柜子名称", "元器件名称", "规格型号", "数量"]

                # 6. 结果展示
                st.subheader("📊 解析结果清单")
                st.dataframe(df, use_container_width=True)

                # 7. Excel 导出
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 点击下载 Excel 表格",
                    data=output.getvalue(),
                    file_name=f"BOM_Result_{uploaded_file.name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        except Exception as e:
            st.error(f"解析过程中出现小状况: {str(e)}")
            st.info("提示：如果结果不完整，建议将 PDF 拆分为单页后重新上传解析。")

# 侧边栏说明
with st.sidebar:
    st.header("使用说明")
    st.write("1. 此工具专门针对电气开关柜图纸优化。")
    st.write("2. 规格型号将尽可能保留图纸上的原始参数。")
    st.write("3. 建议上传清晰的 PDF 原件以获得最高准确率。")
