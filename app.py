import streamlit as st
import google.generativeai as genai
import pandas as pd
import io

# 1. 页面设置
st.set_page_config(page_title="Gemini 3 设计图解析器", layout="centered")

# 2. 配置 API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("请在 Secrets 中配置 GOOGLE_API_KEY")
    st.stop()

st.title("🚀 Gemini 3 元器件解析神器")

# 3. 核心模型选择：使用最新的 Gemini 3 Flash
# 备注：如果报错 404，代码会自动回退到 1.5 版本确保程序不挂
MODELS_TO_TRY = ["gemini-3-flash", "gemini-1.5-flash"]

# 4. 文件上传
uploaded_file = st.file_uploader("上传设计图 (PDF 或图片)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.success(f"文件已就绪: {uploaded_file.name}")
    
    if st.button("✨ 执行 AI 深度解析"):
        response_text = ""
        success = False
        
        with st.spinner("Gemini 3 正在扫描分析中..."):
            for model_name in MODELS_TO_TRY:
                try:
                    model = genai.GenerativeModel(model_name)
                    # 构造多模态内容
                    content = [
                        "你是一个资深电子工程师。请识别图中的元器件清单。直接输出 CSV 格式：名称,数量。不要多余解释。",
                        {"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}
                    ]
                    
                    response = model.generate_content(content)
                    response_text = response.text
                    success = True
                    break
                except Exception as e:
                    continue
            
            if success:
                # 处理 CSV 数据
                try:
                    clean_csv = response_text.replace('```csv', '').replace('```', '').strip()
                    df = pd.read_csv(io.StringIO(clean_csv), names=["元器件名称", "数量"])
                    
                    st.subheader("📊 解析结果清单")
                    st.table(df)

                    # Excel 导出
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    
                    st.download_button("📥 下载 Excel 表格", output.getvalue(), "解析结果.xlsx")
                except:
                    st.warning("解析成功但格式转换失败，原始回复如下：")
                    st.write(response_text)
            else:
                st.error("所有模型调用均失败。请检查 API Key 权限。")
