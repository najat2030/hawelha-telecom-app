import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
from concurrent.futures import ThreadPoolExecutor

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide")

# ================= REGEX =================
phone_pattern = re.compile(r'(01[0125]\d{8})')
number_pattern = re.compile(r'-?\d+(?:\.\d+)?')
arabic_pattern = re.compile(r'[\u0600-\u06FF]')

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    text = phone_pattern.sub('', text)
    return [float(x) for x in number_pattern.findall(text)]

# ================= SMART PARSER =================
def process_file(file):

    records = []

    with pdfplumber.open(file) as pdf:

        # 🔥 Detect language مرة واحدة
        first_page_text = pdf.pages[0].extract_text() or ""
        lang = "ar" if arabic_pattern.search(first_page_text) else "en"

        for page in pdf.pages[2:]:

            # 🔥 Skip الصفحات الفاضية
            if not page.extract_text():
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

                        records.append({
                            "المصدر": file.name,
                            "محمول": str(phone),
                            "رسوم شهرية": values[0] if len(values)>0 else 0,
                            "إجمالي": values[-1] if values else 0
                        })

    return records

# ================= UI =================
st.title("🚀 Hawelha Telecom — Ultra Fast Engine")

files = st.file_uploader(
    "📂 ارفع ملفات PDF",
    type=["pdf"],
    accept_multiple_files=True
)

# ================= PROCESS =================
if files:
    if st.button("🔥 بدء المعالجة السريعة"):

        progress_bar = st.progress(0)
        status_text = st.empty()

        total_files = len(files)
        all_data = []

        # 🔥 Queue processing + Threads
        with ThreadPoolExecutor(max_workers=4) as executor:

            futures = []
            for f in files:
                futures.append(executor.submit(process_file, f))

            for i, future in enumerate(futures):

                result = future.result()
                all_data.extend(result)

                progress = int(((i+1) / total_files) * 100)

                progress_bar.progress(progress)
                status_text.text(f"⚡ تم معالجة {i+1} من {total_files} ملف")

        # ================= OUTPUT =================
        if all_data:
            df = pd.DataFrame(all_data)

            st.success("🎉 تم تحويل كل الملفات بسرعة خارقة")

            # KPI
            c1, c2, c3 = st.columns(3)
            c1.metric("عدد السجلات", len(df))
            c2.metric("إجمالي الرسوم", int(df["رسوم شهرية"].sum()))
            c3.metric("الإجمالي", int(df["إجمالي"].sum()))

            st.dataframe(df.head(20), use_container_width=True)

            # Excel
            output = io.BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            st.download_button(
                "📥 تحميل الملف النهائي",
                output,
                "hawelha_fast.xlsx"
            )
