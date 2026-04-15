import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os

# ================= إعداد الصفحة =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= اختيار اللغة =================
mode = st.radio(
    "🌐 اختر نوع الملف",
    ["Auto 🤖", "عربي 🇪🇬", "English 🌍"],
    horizontal=True
)

# ================= تحميل الشعار =================
def load_logo():
    logo_path = 'static/logo.png'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

# ================= Detect Language =================
def detect_language(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages[:2]:
            text = page.extract_text()
            if text and re.search(r'[\u0600-\u06FF]', text):
                return "ar"
    return "en"

# ================= ARABIC =================
def extract_numbers_from_row(row):
    values = []
    row_text = ' '.join([str(cell).strip() for cell in row if cell])
    numbers = re.findall(r'-?\d+\.?\d*', row_text)
    for num in numbers:
        try:
            values.append(float(num))
        except:
            pass
    return values

def extract_etisalat_data_ar(uploaded_file):
    all_records = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page_num in range(2, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            if not tables:
                continue

            for table in tables:
                i = 0
                while i < len(table):
                    row = table[i]
                    row_text = ' '.join([str(cell) for cell in row if cell])

                    phone_match = re.search(r'(01[0125]\d{8})', row_text)

                    if phone_match:
                        phone = phone_match.group(1)

                        values = extract_numbers_from_row(row)

                        if i + 1 < len(table):
                            next_values = extract_numbers_from_row(table[i + 1])
                            if len(next_values) > len(values):
                                values = next_values
                                i += 1

                        reversed_values = values[::-1]

                        def get_val(idx):
                            return reversed_values[idx] if idx < len(reversed_values) else 0

                        record = {
                            'محمول': phone,
                            'رسوم شهرية': get_val(0),
                            'رسوم الخدمات': get_val(1),
                            'مكالمات محلية': get_val(2),
                            'رسائل محلية': get_val(3),
                            'إنترنت محلية': get_val(4),
                            'مكالمات دولية': get_val(5),
                            'رسائل دولية': get_val(6),
                            'مكالمات تجوال': get_val(7),
                            'رسائل تجوال': get_val(8),
                            'إنترنت تجوال': get_val(9),
                            'رسوم وتسويات اخري': get_val(10),
                            'قيمة الضرائب': get_val(11),
                            'إجمالي': get_val(12)
                        }

                        all_records.append(record)

                    i += 1

    return all_records

# ================= ENGLISH =================
def extract_values_from_row(row):
    values = []
    row_text = ' '.join([str(cell).strip() for cell in row if cell])
    numbers = re.findall(r'-?\d+\.?\d*', row_text)

    for num in numbers:
        try:
            values.append(float(num))
        except:
            pass

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

def extract_etisalat_data_en(uploaded_file):
    all_records = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page_num in range(2, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            if tables:
                for table in tables:
                    i = 0
                    while i < len(table):
                        row = table[i]
                        row_text = ' '.join([str(cell) for cell in row if cell])

                        phone_match = re.search(r'(01[0125]\d{8})', row_text)

                        if phone_match:
                            phone = phone_match.group(1)

                            if i + 1 < len(table):
                                values = extract_values_from_row(table[i + 1])
                                record = create_record(phone, values)
                                all_records.append(record)
                                i += 2
                                continue

                        i += 1

    return all_records

# ================= Excel =================
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# ================= UI =================
st.title("📊 Hawelha Telecom")

uploaded_file = st.file_uploader("📁 ارفع ملف PDF", type=["pdf"])

if uploaded_file:
    st.success(f"تم رفع: {uploaded_file.name}")

    if st.button("🚀 بدء التحويل"):
        with st.spinner("جاري المعالجة..."):

            if mode == "Auto 🤖":
                lang = detect_language(uploaded_file)
            elif mode == "عربي 🇪🇬":
                lang = "ar"
            else:
                lang = "en"

            if lang == "ar":
                records = extract_etisalat_data_ar(uploaded_file)
            else:
                records = extract_etisalat_data_en(uploaded_file)

            if records:
                df = pd.DataFrame(records)

                st.success(f"تم استخراج {len(df)} سجل")

                st.dataframe(df.head(10))

                excel = convert_df_to_excel(df)

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name="hawelha.xlsx"
                )
            else:
                st.error("لم يتم العثور على بيانات")
