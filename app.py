
   import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# 1. 页面设置：设置标题和居中布局
st.set_page_config(page_title="设计图元器件解析器", layout="centered")

# 2. 注入 CSS：复刻 AI Studio 的高级感排版
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stApp { max-width: 850px; margin: 0 auto; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        background-color: #059669; 
        color: white; 
        height: 3.5em; 
        font-weight: bold;
        border: none;
    }
    .upload-hint { 
        padding: 50px; 
        border: 2px dashed #d1d5db; 
        border-radius: 15px; 
        text-align: center; 
        background-color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 标题区
st.markdown("<h2 style='text-align: center; color: #111827;'>✨ 设计图元器件解析器</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6b7280; margin-bottom: 30px;'>AI POWERED ANALYSIS & EXPORT</p>", unsafe_allow_html=True)

# 3. 配置 API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ 还没配置 API Key 呢！请在 Streamlit 后台 Secrets 设置。")
    st.stop()

# 4. 文件上传组件
uploaded_file = st.file_uploader("上传设计图 (支持 PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

if uploaded_file is not None:
    # 预览区域
    if uploaded_file.type != "application/pdf":
        image = Image.open(uploaded_file)
        st.image(image, caption="待解析的设计图", use_container_width=True)
    else:
        st.info("📂 已加载 PDF 文档，准备进行全页扫描解析...")

    # 5. 解析逻辑
    if st.button("🚀 开始智能解析"):
        # 使用 Flash 模型（速度快，适合解析表格数据）
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 严谨的 Prompt：要求 AI 只输出 CSV 格式，方便后续导出 Excel
        prompt = """
        你是一个精通电子工程和工业设计图的专家。
        请识别图中（或PDF文档中）的所有元器件。
        要求：
        1. 仅输出 CSV 格式的数据。
        2. 包含两列：元器件名称, 数量。
        3. 不要输出任何多余的开场白、解释或 Markdown 代码块标签（如 ```csv）。
        
        输出示例：
        电阻, 10
        电容, 5
        IC芯片, 2
        """
        
        with st.spinner("🤖 AI 正在深度扫描，请稍候..."):
            try:
                # 处理不同类型的文件输入
                if uploaded_file.type == "application/pdf":
                    # 针对 PDF 必须明确 mime_type 包装，防止 TypeError
                    content = [prompt, {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}]
                else:
                    content = [prompt, image]
                
                response = model.generate_content(content)
                
                # 清洗 AI 返回的文本（去掉可能存在的 Markdown 标签）
                raw_text = response.text
                clean_text = raw_text.replace('```csv', '').replace('```', '').strip()
                
                # 6. 数据处理与导出
                df = pd.read_csv(io.StringIO(clean_text), names=["元器件名称", "数量"])
                
                st.markdown("### 📊 解析结果清单")
                st.table(df) # 展示漂亮的原生表格

                # 生成 Excel 二进制流
                excel_data = io.BytesIO()
                with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='元器件清单')
                
                # 下载按钮
                st.download_button(
                    label="📥 下载 Excel 结果表格",
                    data=excel_data.getvalue(),
                    file_name="元器件解析结果.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"解析过程中出现小状况：{str(e)}")
                st.info("您可以尝试重新点击解析按钮，或者检查图片是否清晰。")
else:
    # 未上传文件时的占位图，模仿 AI Studio 效果
    st.markdown("""
        <div class="upload-hint">
            <p style="font-size: 50px;">📄</p>
            <h4 style="color: #374151;">等待解析</h4>
            <p style="color: #6b7280;">上传您的设计图并点击“开始智能解析”按钮，<br>AI 将自动为您提取元器件清单并生成 Excel。</p>
        </div>
    """, unsafe_allow_html=True)
