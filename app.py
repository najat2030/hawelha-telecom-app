import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= MODE =================
mode = st.radio(
    "🌐 اختر نوع الملف",
    ["Auto 🤖", "عربي 🇪🇬", "English 🌍"],
    horizontal=True
)

# ================= LOGO =================
def load_logo():
    logo_path = 'static/logo.png'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

# ================= TEXT NORMALIZATION (FIX NEGATIVE ISSUE) =================
def normalize_text(text):
    if not text:
        return ""
    text = text.replace("−", "-")  # Unicode minus
    text = text.replace("–", "-")
    return text

# ================= AUTO DETECT =================
def detect_language(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages[:2]:
            text = page.extract_text()
            if text and re.search(r'[\u0600-\u06FF]', text):
                return "ar"
    return "en"

# ================= COMMON NUMBER EXTRACTION =================
def extract_numbers(row_text):
    row_text = normalize_text(row_text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', row_text)

    values = []
    for n in numbers:
        try:
            values.append(float(n))
        except:
            pass
    return values

# ================= ARABIC =================
def extract_etisalat_data_ar(uploaded_file):
    records = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page_num in range(2, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            for table in tables or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue

                    row_text = normalize_text(' '.join([str(c) for c in row if c]))

                    phone_match = re.search(r'(01[0125]\d{8})', row_text)

                    if phone_match:
                        phone = phone_match.group(1)

                        values = extract_numbers(row_text)

                        if i + 1 < len(table):
                            next_vals = extract_numbers(' '.join([str(c) for c in table[i+1] if c]))
                            if len(next_vals) > len(values):
                                values = next_vals
                                i += 1

                        values = values[::-1]

                        def g(i):
                            return values[i] if i < len(values) else 0

                        records.append({
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
                            'إجمالي': g(12)
                        })

                    i += 1

    return records

# ================= ENGLISH =================
def extract_etisalat_data_en(uploaded_file):
    records = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page_num in range(2, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            for table in tables or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue

                    row_text = ' '.join([str(c) for c in row])

                    phone_match = re.search(r'(01[0125]\d{8})', row_text)

                    if phone_match:
                        phone = phone_match.group(1)

                        values = extract_numbers(
                            ' '.join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else ""
                        )

                        records.append({
                            'محمول': phone,
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
                            'رسوم وتسويات اخري': values[10] if len(values)>10 else 0,
                            'قيمة الضرائب': values[11] if len(values)>11 else 0,
                            'إجمالي': values[12] if len(values)>12 else (values[-1] if values else 0)
                        })

                        i += 2
                        continue

                    i += 1

    return records

# ================= EXCEL =================
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# ================= UI =================
st.title("📊 Hawelha Telecom")

uploaded_file = st.file_uploader("📁 ارفع PDF", type=["pdf"])

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
                    file_name="hawelha.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("لم يتم العثور على بيانات")
