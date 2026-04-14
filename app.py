import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os
import tabula

# ========== إعدادات الصفحة ==========
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== تحميل الشعار ==========
def load_logo():
    logo_path = 'static/logo.png'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode()
            return logo_data
    return None

# ========== CSS ==========
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
* { font-family: 'Cairo', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: white;
    padding: 2.5rem 2rem;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 2rem;
}
</style>""", unsafe_allow_html=True)

# ========== الهيدر ==========
logo_data = load_logo()

if logo_data:
    st.markdown(f"""
    <div class="main-header">
        <img src="data:image/png;base64,{logo_data}" style="max-height:200px;">
        <p>احترافي • سريع • دقيق</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>Hawelha Telecom</h1>
    </div>
    """, unsafe_allow_html=True)

# ========== استخراج باستخدام Tabula ==========
def extract_with_tabula(uploaded_file):
    dfs = tabula.read_pdf(
        uploaded_file,
        pages='3-end',
        multiple_tables=True
    )

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    return df

# ========== تحويل للإكسل ==========
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# ========== الواجهة ==========
uploaded_file = st.file_uploader("📁 ارفع ملف PDF", type=['pdf'])

if uploaded_file is not None:
    if st.button("🚀 بدء التحويل"):
        with st.spinner("جاري المعالجة..."):

            df = extract_with_tabula(uploaded_file)

            if not df.empty:

                # ⚠️ هنا هنظبط الأعمدة يدوي (مؤقتًا)
                df.columns = [
                    'محمول',
                    'رسوم شهرية',
                    'رسوم الخدمات',
                    'مكالمات محلية',
                    'رسائل محلية',
                    'إنترنت محلية',
                    'مكالمات دولية',
                    'رسائل دولية',
                    'مكالمات تجوال',
                    'رسائل تجوال',
                    'إنترنت تجوال',
                    'رسوم وتسويات اخرى',
                    'قيمة الضرائب',
                    'إجمالي'
                ]

                # ترتيب الأعمدة
                columns_order = [
                    'محمول',
                    'رسوم شهرية',
                    'رسوم الخدمات',
                    'مكالمات محلية',
                    'رسائل محلية',
                    'إنترنت محلية',
                    'مكالمات دولية',
                    'رسائل دولية',
                    'مكالمات تجوال',
                    'رسائل تجوال',
                    'إنترنت تجوال',
                    'رسوم وتسويات اخرى',
                    'قيمة الضرائب',
                    'إجمالي'
                ]

                df = df[columns_order]

                st.dataframe(df.head(10))

                excel_file = convert_df_to_excel(df)

                st.download_button(
                    label="📥 تحميل Excel",
                    data=excel_file,
                    file_name="hawelha_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.error("لم يتم استخراج بيانات")
