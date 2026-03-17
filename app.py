
import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import io

# 1. 页面配置：设置标题和居中布局
st.set_page_config(page_title="设计图元器件解析器", layout="centered")

# 2. 注入 CSS 提升视觉高级感
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #059669; color: white; height: 3em; font-weight: bold; }
    .upload-hint { padding: 40px; border: 2px dashed #d1d5db; border-radius: 12px; text-align: center; color: #6b7280; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>✨ 设计图元器件解析器</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6b7280;'>AI POWERED ANALYSIS & EXPORT</p>", unsafe_allow_html=True)

# 3. 配置 API Key
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("请在 Streamlit Secrets 中配置 GOOGLE_API_KEY")
    st.stop()

# 4. 上传组件
uploaded_file = st.file_uploader("上传设计图 (支持 PNG, JPG, PDF)", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file is not None:
    # 处理文件流
    if uploaded_file.type == "application/pdf":
        st.warning("注：PDF 解析功能需要后端支持图片转换。建议优先使用图片格式。")
        # 这里简化处理：提示用户。如果需要完美解析PDF每一页，通常需要安装poppler，Streamlit Cloud环境较复杂
        # 暂时将PDF作为文档流尝试，或建议用户转为图片
        st.info("正在尝试直接解析文档...")
    
    image = Image.open(uploaded_file) if uploaded_file.type != "application/pdf" else None
    if image:
        st.image(image, caption="待解析的设计图", use_container_width=True)

    # 点击解析按钮
 if st.button("🚀 开始智能解析"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        请仔细分析这张设计图（如果是PDF请扫描所有页面），识别出所有的元器件。
        请仅输出一个 CSV 格式的列表，包含两列：元器件名称, 数量。
        不要输出任何额外的解释文字，直接给数据。
        例如：
        电阻, 10
        电容, 5
        """
        
        with st.spinner("AI 正在扫描文档并计算元器件..."):
            try:
                # 核心修复逻辑：根据文件类型打包数据
                if uploaded_file.type == "application/pdf":
                    # PDF 需要包装成字典格式
                    doc_content = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                    response = model.generate_content([prompt, doc_content])
                else:
                    # 图片直接发送
                    response = model.generate_content([prompt, image])
                
                # ... 后面转换表格的代码保持不变 ...            
            # 5. 处理结果并转为 Excel
            try:
                # 将 AI 返回的文字转换为 Pandas 表格
                data = io.StringIO(response.text)
                df = pd.read_csv(data, names=["元器件名称", "数量"])
                
                st.success("解析完成！")
                st.table(df) # 在网页展示表格

                # 生成 Excel 文件供下载
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Sheet1')
                
                st.download_button(
                    label="📥 点击下载 Excel 结果",
                    data=output.getvalue(),
                    file_name="元器件清单.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error("解析格式转换失败，AI 原始回复如下：")
                st.write(response.text)

else:
    # 等待上传的占位展示
    st.markdown("""
        <div class="upload-hint">
            <p style="font-size: 40px;">📄</p>
            <h4>等待解析</h4>
            <p>上传您的设计图并点击按钮，AI 将自动提取元器件清单并提供 Excel 下载。</p>
        </div>
    """, unsafe_allow_html=True)
