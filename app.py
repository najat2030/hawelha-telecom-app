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
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
* { font-family: 'Cairo', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: white;
    padding: 2.5rem;
    border-radius: 15px;
    text-align: center;
}
.upload-box {
    background: #f0fdf4;
    border: 3px dashed #10b981;
    border-radius: 15px;
    padding: 3rem;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ========== UI ==========
logo = load_logo()

if logo:
    st.markdown(f"""
    <div class="main-header">
        <img src="data:image/png;base64,{logo}" style="max-height:200px;">
        <p>تحويل فواتير اتصالات من PDF إلى Excel</p>
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

# ================== SMART ENGINE ==================

def extract_etisalat_data(file):
    all_records = []

    with pdfplumber.open(file) as pdf:
        for i in range(2, len(pdf.pages)):
            text = pdf.pages[i].extract_text()
            if text:
                all_records.extend(parse_text_page(text))

    return all_records


def parse_text_page(text):
    records = []
    lines = text.split('\n')
    current_phone = None

    for line in lines:

        phone = re.search(r'(01[0125]\d{8})', line)
        if phone:
            current_phone = phone.group(1)
            continue

        numbers = extract_numbers(line)

        if current_phone and len(numbers) >= 5:
            values = normalize(numbers)
            record = create_record(current_phone, values)
            record = validate(record)

            records.append(record)
            current_phone = None

    return records


def extract_numbers(text):
    nums = re.findall(r'-?\d+\.\d+', text)

    if not nums:
        chunks = re.findall(r'[-\d\.]{8,}', text)
        for c in chunks:
            nums.extend(re.findall(r'-?\d+\.\d{2}', c))

    return nums


def normalize(nums):
    clean = []
    for n in nums:
        try:
            clean.append(float(n))
        except:
            pass
    return clean


def create_record(phone, values):
    def g(i):
        return values[i] if i < len(values) else 0

    return {
        'محمول': phone,
        'رسوم شهرية': g(0),
        'رسوم الخدمات': g(1),
        'مكالمات محلية': g(2),
        'رسائل محلية': g(3),
        'إنترنت محلية': g(4),
        'مكالمات دولية': g(5),
        'رسائل دولية': g(6),
        'مكالمات تجوال': g(7),
        'رسائل تجوال': g(8),
        'إنترنت تجوال': g(9),
        'رسوم وتسويات اخري': g(10),
        'قيمة الضرائب': g(11),
        'إجمالي': g(12) if len(values) > 12 else (values[-1] if values else 0)
    }


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
                st.error("لم يتم استخراج بيانات")
