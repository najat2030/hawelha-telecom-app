import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
from concurrent.futures import ThreadPoolExecutor

# ================= CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom",
    layout="wide"
)

# ================= REGEX OPTIMIZED =================
phone_pattern = re.compile(r'(01[0125]\d{8})')
number_pattern = re.compile(r'-?\d+(?:\.\d+)?')

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    text = phone_pattern.sub('', text)
    return [float(x) for x in number_pattern.findall(text)]

# ================= PARSE FILE =================
def process_file(file, mode):

    records = []

    with pdfplumber.open(file) as pdf:

        if mode == "Auto":
            text = pdf.pages[0].extract_text() or ""
            lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
        else:
            lang = mode

        for page in pdf.pages[2:]:
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                for row in table:
                    if not row:
                        continue

                    text = " ".join([str(c) for c in row if c])
                    match = phone_pattern.search(text)

                    if match:
                        phone = match.group(1)
                        values = extract_numbers(text)

                        records.append({
                            "المصدر": file.name,
                            "محمول": str(phone),
                            "رسوم شهرية": values[0] if len(values)>0 else 0,
                            "إجمالي": values[-1] if values else 0
                        })

    return records

# ================= UI =================
st.title("🚀 Hawelha Telecom - Fast Mode")

files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

mode = st.selectbox("Mode", ["Auto", "ar", "en"])

# ================= FAST PROCESS =================
if files:
    if st.button("🔥 Start Fast Processing"):

        all_data = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(lambda f: process_file(f, mode), files)

        for r in results:
            all_data.extend(r)

        if all_data:
            df = pd.DataFrame(all_data)

            st.success(f"⚡ تم معالجة {len(files)} ملف بسرعة")

            st.dataframe(df.head(20))

            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.download_button("📥 Download Excel", output, "fast_output.xlsx")
