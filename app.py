import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
import re

# 1. 页面基本配置：设置标题和居中布局
st.set_page_config(page_title="电气设计图智能解析系统", layout="centered")

# 标题区：使用 HTML 装修，让标题更醒目
st.markdown("<h2 style='text-align: center; color: #1f2937;'>✨ 电气设计图智能解析系统</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6b7280; margin-bottom: 30px;'>AI POWERED ENGINEERING B.O.M. ANALYSIS</p>", unsafe_allow_html=True)

# 2. 安全读取 API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("⚠️ 未在 Streamlit Secrets 中发现 API Key，请检查配置。")
    st.stop()

# 3. 动态识别最新模型（在后台无声检测）
@st.cache_resource
def get_best_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 按照性能和免费额度排序：优先调用 2.5 Flash
        for preferred in ['models/gemini-2.5-flash', 'models/gemini-1.5-flash']:
            if preferred in models:
                return preferred
        return models[0] if models else "gemini-1.5-flash"
    except Exception:
        return "gemini-1.5-flash"

active_model = get_best_model()

# 将引擎信息隐藏在侧边栏中供排查使用
with st.sidebar:
    st.markdown("### 🛠️ 系统诊断")
    st.write(f"当前调用的 AI 引擎：`{active_model}`")

# 4. 上传组件：文案已调整， label_visibility="collapsed" 隐藏默认标签
uploaded_file = st.file_uploader("请上传电气设计图纸 (支持 PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")

# 5. 上传提示占位
if uploaded_file is None:
    st.markdown("""
        <div style="padding: 50px; border: 2px dashed #d1d5db; border-radius: 15px; text-align: center; background-color: #f9fafb;">
            <p style="font-size: 50px;">📄</p>
            <h4 style="color: #374151;">等待上传</h4>
            <p style="color: #6b7280;">上传您的电气设计图 (PDF/PNG/JPG)，<br>AI 将自动为您生成工程级 BOM 结果。</p>
        </div>
    """, unsafe_allow_html=True)

# --- 定义一个全局状态变量来存储 DataFrame，以便解析完成后能保持在页面上 ---
if 'parsed_df' not in st.session_state:
    st.session_state.parsed_df = None

# --- 文件上传后的逻辑 ---
if uploaded_file is not None:
    # 预览区域
    if uploaded_file.type != "application/pdf":
        # 图片预览
        st.markdown("### 📷 图纸预览")
        st.image(uploaded_file, use_container_width=True)
    else:
        # PDF 预览（Streamlit 目前支持较弱，显示占位）
        st.info(f"📂 已加载 PDF 文档：`{uploaded_file.name}`，准备进行全页扫描解析...")

    # 6. 解析按钮
    if st.button("🚀 开始智能工程级解析", use_container_width=True):
        try:
            model = genai.GenerativeModel(active_model)
            
            # --- 精装修 Prompt：专门针对电气成套开关柜优化 ---
            prompt = """
            你是一个精通电气工程设计图纸的专家。请深度解析此文件（PDF或图片）。
            目标：提取出一份高精度的电气系统成套 BOM 清单。
            
            要求如下：
            1. **分柜识别**：必须识别出图纸中的每一个独立的柜体（如：#1进线柜 AH1、PT柜、电容柜、馈线柜等）。
            2. **对应关系**：明确每一个元器件属于哪个具体的柜体。
            3. **提取维度**：对于每个元器件，必须准确提取出以下四个维度的信息，特别是完整的规格型号（需包含所有参数信息，如 A, V, 3P/4P, 材质, 参数等级等）。
            4. **禁忌事项**：仅输出严格的 CSV 格式，包含以下四列：柜子名称,元器件名称,规格型号,数量。
            5. **不要输出任何Markdown标签**(如 ```csv)、不要解释性文字、不要空行。
            
            输出示例：
            柜子名称,元器件名称,规格型号,数量
            AH1进线柜,框架断路器,MT12H1 3P 1250A Micrologic 2.0A,1
            AH1进线柜,电流互感器 CT,AKH-0.66/I 100/5A,3
            AH2电容柜,自愈式电容器,BSMJ0.45-20-3,10
            AH2馈线柜,塑壳断路器,NSX100F 3P 80A,5
            """
            
            with st.spinner("🤖 AI 正在深度解析柜体结构、元器件和完整规格型号，请稍候..."):
                # 针对不同文件打包数据
                if uploaded_file.type == "application/pdf":
                    # 对 PDF 进行全页扫描需要 MIME_TYPE 包装
                    content_parts = [prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                else:
                    # 图片直接发送
                    content_parts = [prompt, uploaded_file]
                
                response = model.generate_content(content_parts)
                
                # 清洗数据
                raw_text = response.text
                # 移除可能存在的 Markdown 标签（如 ```csv）
                clean_csv = re.sub(r'```[a-zA-Z]*\n?', '', raw_text).strip()
                
                # 将 CSV 转换为 DataFrame
                # read_csv 时会自动识别表头并对齐列
                # prompt 里已经强制输出表头，所以这里不需要names参数
                df = pd.read_csv(io.StringIO(clean_csv), sep=',')
                
                # 统一表头名称，确保即使用户的 CSV 表头微差，最终 DataFrame 的表头是我们要的
                df.columns = ["柜子名称", "元器件名称", "规格型号", "数量"]
                
                # 将 DataFrame 存储到 st.session_state 中，防止页面刷新消失
                st.session_state.parsed_df = df
                st.session_state.download_filename = uploaded_file.name

        except Exception as e:
            st.error(f"发生解析错误：{str(e)}")
            st.info("提示：请确保图纸清晰，如果错误依然存在，请重置 Streamlit 后台 Secrets 中的 GOOGLE_API_KEY。")

# 7. 解析结果持久展示区域
# 只有当 session_state 里的 df 不为空时才展示
if st.session_state.parsed_df is not None:
    df = st.session_state.parsed_df
    filename = st.session_state.download_filename
    
    st.markdown("---") # 分割线
    st.markdown("### 📊 工程级 B.O.M. 解析结果")
    
    # 装修数据展示区：使用 dataframe 组件，增加宽度和可交互性
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True, # 隐藏索引列（Row Index）
    )

    # 生成 Excel 二进制流
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='解析清单')
    
    excel_data = output.getvalue()

    # 结果下方展示 Excel 下载按钮
    st.download_button(
        label="📥 下载 Excel 结果表格",
        data=excel_data,
        file_name=f"BOM解析结果_{filename}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
