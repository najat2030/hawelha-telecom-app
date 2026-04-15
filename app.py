import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

st.set_page_config(page_title="Hawelha Telecom", layout="wide")

phone_pattern = re.compile(r'(01[0125]\d{8})')
number_pattern = re.compile(r'-?\d+(?:\.\d+)?')
arabic_pattern = re.compile(r'[\u0600-\u06FF]')

def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    text = phone_pattern.sub('', text)
    return [float(x) for x in number_pattern.findall(text)]

def process_files(files):

    all_records = []

    for file in files:
        try:
            with pdfplumber.open(file) as pdf:

                if not pdf.pages:
                    continue

                first_text = pdf.pages[0].extract_text() or ""
                lang = "ar" if arabic_pattern.search(first_text) else "en"

                for page in pdf.pages[2:]:

                    try:
                        text_page = page.extract_text()
                        if not text_page:
                            continue

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

                                    all_records.append({
                                        "المصدر": file.name,
                                        "محمول": phone,
                                        "رسوم شهرية": values[0] if len(values)>0 else 0,
                                        "إجمالي": values[-1] if values else 0
                                    })

                    except:
                        continue

        except:
            st.warning(f"⚠️ ملف فيه مشكلة وتم تخطيه: {file.name}")
            continue

    return all_records

# UI
st.title("⚡ Hawelha Telecom — Stable Version")

files = st.file_uploader("📂 ارفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 Start Processing"):

        with st.spinner("⚡ جاري التحويل..."):

            data = process_files(files)

        if data:
            df = pd.DataFrame(data)

            st.success("🎉 تم التحويل بنجاح")

            st.dataframe(df.head(20), use_container_width=True)

            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.download_button("📥 تحميل Excel", output, "hawelha.xlsx")

        else:
            st.error("❌ لم يتم استخراج بيانات")
