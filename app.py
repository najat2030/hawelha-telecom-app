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
            return base64.b64encode(f.read()).decode()
    return None

# ========== CSS ==========
st.markdown("""
<style>
* { font-family: 'Cairo', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: white;
    padding: 2.5rem;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 2rem;
}

.upload-box {
    background: #f0fdf4;
    border: 2px dashed #10b981;
    border-radius: 15px;
    padding: 2rem;
    text-align: center;
}

.file-name {
    text-align:center;
    margin-top:10px;
    color:#065f46;
    font-weight:600;
}

.stButton>button {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: white;
    border-radius: 8px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ========== الهيدر ==========
logo = load_logo()

if logo:
    st.markdown(f"""
    <div class="main-header">
        <img src="data:image/png;base64,{logo}" style="max-height:200px;">
        <p>احترافي • سريع • دقيق</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>Hawelha Telecom | حوّلها</h1>
        <p>احترافي • سريع • دقيق</p>
    </div>
    """, unsafe_allow_html=True)

# ========== استخراج البيانات ==========
def extract_values_from_row(row):
    values = []
    for cell in reversed(row):
        if not cell:
            continue
        numbers = re.findall(r'-?\d+\.?\d*', str(cell))
        for n in numbers:
            values.append(float(n))
    return values

def parse_table(table):
    records = []
    i = 0
    while i < len(table):
        row = table[i]
        row_text = ' '.join([str(c) if c else '' for c in row])

        phone = re.search(r'(01[0125]\d{8})', row_text)
        if phone:
            values = []
            if i+1 < len(table):
                values = extract_values_from_row(table[i+1])

            records.append({
                'محمول': phone.group(1),
                'رسوم شهرية': values[0] if len(values)>0 else 0,
                'رسوم الخدمات': values[1] if len(values)>1 else 0,
                'مكالمات محلية': values[2] if len(values)>2 else 0,
                'رسائل محلية': values[3] if len(values)>3 else 0,
                'إنترنت محلية': values[4] if len(values)>4 else 0,
                'مكالمات دولية': values[5] if len(values)>5 else 0,
                'رسائل دولية': values[6] if len(values)>6 else 0,
                'مكالمات تجوال': values[7] if len(values)>7 else 0,
                'رسائل تجوال': values[8] if len(values)>8 else 0,
                'إنترنت تجوال': values[9] if len(values)>9 else 0,
                'رسوم وتسويات اخرى': values[10] if len(values)>10 else 0,
                'قيمة الضرائب': values[11] if len(values)>11 else 0,
                'إجمالي': values[12] if len(values)>12 else (values[-1] if values else 0)
            })
            i += 2
        else:
            i += 1

    return records

def extract_data(file):
    all_records = []
    with pdfplumber.open(file) as pdf:
        for i in range(2, len(pdf.pages)):
            tables = pdf.pages[i].extract_tables()
            if tables:
                for t in tables:
                    all_records.extend(parse_table(t))
    return all_records

# ========== تحويل لإكسل ==========
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ========== الواجهة ==========
st.markdown('<div class="upload-box"><h3>ارفع ملف PDF</h3></div>', unsafe_allow_html=True)

file = st.file_uploader("", type="pdf")

if file:
    st.markdown(f'<div class="file-name">{file.name}</div>', unsafe_allow_html=True)

    if st.button("🚀 بدء التحويل"):
        with st.spinner("جاري المعالجة..."):
            records = extract_data(file)

            if records:
                df = pd.DataFrame(records)

                st.dataframe(df.head(10))

                excel = to_excel(df)

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name=f"hawelha_{datetime.now().strftime('%Y%m%d')}.xlsx"
                )
            else:
                st.error("لم يتم استخراج بيانات")
