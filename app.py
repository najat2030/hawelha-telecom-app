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
    layout="wide"
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
.main-header {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
}
.upload-box {
    border: 2px dashed #10b981;
    padding: 2rem;
    border-radius: 10px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ========== UI ==========
logo = load_logo()

if logo:
    st.markdown(f"""
    <div class="main-header">
        <img src="data:image/png;base64,{logo}" style="max-height:180px;">
        <p>تحويل فواتير الاتصالات من PDF إلى Excel</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>Hawelha Telecom</h1>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="upload-box">
<h3>📁 ارفع ملف PDF</h3>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["pdf"])

# ================== ENGINE ==================

def extract_etisalat_data(file):
    records = []

    with pdfplumber.open(file) as pdf:
        for page_num in range(2, len(pdf.pages)):
            page = pdf.pages[page_num]

            words = page.extract_words(use_text_flow=True)

            # استخراج الأرقام
            numbers = [
                w for w in words
                if re.match(r'-?\d+\.\d+', w['text'])
            ]

            # استخراج أرقام الموبايل
            phones = [
                w for w in words
                if re.match(r'01[0125]\d{8}', w['text'])
            ]

            for phone in phones:
                phone_y = phone['top']

                # الأرقام في نفس السطر
                row_numbers = [
                    n for n in numbers
                    if abs(n['top'] - phone_y) < 5
                ]

                # ترتيب عربي (يمين → شمال)
                row_numbers = sorted(row_numbers, key=lambda x: -x['x0'])

                values = []
                for n in row_numbers:
                    try:
                        values.append(float(n['text']))
                    except:
                        pass

                record = create_record(phone['text'], values)
                record = validate(record)

                records.append(record)

    return records

# ================== RECORD ==================

def create_record(phone, values):
    keys = [
        'رسوم شهرية','رسوم الخدمات','مكالمات محلية','رسائل محلية',
        'إنترنت محلية','مكالمات دولية','رسائل دولية',
        'مكالمات تجوال','رسائل تجوال','إنترنت تجوال',
        'رسوم وتسويات اخري','قيمة الضرائب','إجمالي'
    ]

    record = {'محمول': phone}

    for i, key in enumerate(keys):
        record[key] = values[i] if i < len(values) else 0

    return record

# ================== VALIDATION ==================

def validate(record):
    total_calc = sum([
        record['رسوم شهرية'], record['رسوم الخدمات'],
        record['مكالمات محلية'], record['رسائل محلية'],
        record['إنترنت محلية'], record['مكالمات دولية'],
        record['رسائل دولية'], record['مكالمات تجوال'],
        record['رسائل تجوال'], record['إنترنت تجوال'],
        record['رسوم وتسويات اخري'], record['قيمة الضرائب']
    ])

    if abs(total_calc - record['إجمالي']) > 5:
        record['⚠️ فرق'] = round(total_calc - record['إجمالي'], 2)

    return record

# ================== EXCEL ==================

def to_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer

# ================== RUN ==================

if uploaded_file:
    st.success("تم رفع الملف ✅")

    if st.button("🚀 تحويل"):
        with st.spinner("جاري التحويل..."):

            data = extract_etisalat_data(uploaded_file)

            if data:
                df = pd.DataFrame(data)

                cols = [
                    'محمول','رسوم شهرية','رسوم الخدمات',
                    'مكالمات محلية','رسائل محلية','إنترنت محلية',
                    'مكالمات دولية','رسائل دولية',
                    'مكالمات تجوال','رسائل تجوال','إنترنت تجوال',
                    'رسوم وتسويات اخري','قيمة الضرائب','إجمالي'
                ]

                df = df[cols]

                st.dataframe(df.head(10))

                excel = to_excel(df)

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name=f"hawelha_{datetime.now().strftime('%Y%m%d')}.xlsx"
                )

            else:
                st.error("❌ لم يتم استخراج بيانات")
