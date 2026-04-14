import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os

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
        box-shadow: 0 4px 15px rgba(5,150,105,0.3);
    }
</style>""", unsafe_allow_html=True)

# ========== Sidebar ==========
with st.sidebar:
    st.title("📋 قائمة التحويل")

# ========== Header ==========
logo_data = load_logo()

if logo_data:
    st.markdown(f"""
    <div class="main-header">
        <img src="data:image/png;base64,{logo_data}" width="300">
        <p>احترافي • سريع • دقيق</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Hawelha Telecom</h1>
    </div>
    """, unsafe_allow_html=True)

# ========== استخراج البيانات ==========
def extract_values_from_row(row):
    values = []
    for cell in reversed(row):
        if cell:
            numbers = re.findall(r'-?\d+\.?\d*', str(cell))
            values.extend([float(n) for n in numbers])
    return values


def create_record(phone, values):
    return {
        'محمول': phone,
        'رسوم شهرية': values[0] if len(values) > 0 else 0,
        'رسوم الخدمات': values[1] if len(values) > 1 else 0,
        'مكالمات محلية': values[2] if len(values) > 2 else 0,
        'رسائل محلية': values[3] if len(values) > 3 else 0,
        'إنترنت محلية': values[4] if len(values) > 4 else 0,
        'مكالمات دولية': values[5] if len(values) > 5 else 0,
        'رسائل دولية': values[6] if len(values) > 6 else 0,
        'مكالمات تجوال': values[7] if len(values) > 7 else 0,
        'رسائل تجوال': values[8] if len(values) > 8 else 0,
        'إنترنت تجوال': values[9] if len(values) > 9 else 0,
        'رسوم وتسويات اخري': values[10] if len(values) > 10 else 0,
        'قيمة الضرائب': values[11] if len(values) > 11 else 0,
        'إجمالي': values[12] if len(values) > 12 else (values[-1] if values else 0)
    }


def parse_etisalat_table(table):
    records = []
    i = 0
    while i < len(table):
        row_text = ' '.join([str(c) if c else '' for c in table[i]])
        match = re.search(r'(01[0125]\d{8})', row_text)

        if match:
            phone = match.group(1)
            values = extract_values_from_row(table[i+1]) if i+1 < len(table) else []
            records.append(create_record(phone, values))
            i += 2
        else:
            i += 1

    return records


def extract_etisalat_data(file):
    all_records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            tables = page.extract_tables()
            for table in tables:
                all_records.extend(parse_etisalat_table(table))
    return all_records


def convert_df_to_excel(df):
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()

# ========== UI ==========
uploaded_file = st.file_uploader("📁 ارفع ملف PDF", type=["pdf"])

if uploaded_file:
    if st.button("🚀 بدء التحويل"):
        records = extract_etisalat_data(uploaded_file)

        if records:
            df = pd.DataFrame(records)

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
                'رسوم وتسويات اخري',
                'قيمة الضرائب',
                'إجمالي'
            ]

            df = df.reindex(columns=columns_order)

            st.dataframe(df)

            st.download_button(
                "📥 تحميل Excel",
                convert_df_to_excel(df),
                "output.xlsx"
            )
        else:
            st.error("❌ مفيش بيانات")
