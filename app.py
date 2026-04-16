import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Hawelha Telecom", layout="wide")

st.title("📂 Upload Multiple PDF Invoices")

# رفع ملفات متعددة
files = st.file_uploader(
    "Upload PDF invoices",
    type=["pdf"],
    accept_multiple_files=True
)

all_data = []

def parse_ar(pdf_file):
    rows = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:

            text = page.extract_text() or ""

            # ✂️ قص قبل خدمة الفوترة التحليلية
            if "خدمة الفوترة التحليلية" in text:
                text = text.split("خدمة الفوترة التحليلية")[0]

            tables = page.extract_tables() or []

            for table in tables:

                # ✂️ قص الجدول عند بداية الجزء التقيل
                new_table = []
                stop = False

                for row in table:
                    row_text = " ".join([str(c) for c in row if c])

                    if "خدمة الفوترة التحليلية" in row_text:
                        stop = True
                        break

                    new_table.append(row)

                table = new_table

                for row in table:
                    if not row:
                        continue

                    rows.append(row)

    return rows


if files:
    progress = st.progress(0)
    total = len(files)

    for i, file in enumerate(files):
        try:
            data = parse_ar(file)
            all_data.extend(data)

        except Exception as e:
            st.warning(f"⚠️ مشكلة في ملف: {file.name}")

        progress.progress((i + 1) / total)

    if all_data:
        df = pd.DataFrame(all_data)

        st.success("✅ تم التحويل بنجاح")

        # 📊 Dashboard (بدون تغيير)
        col1, col2, col3, col4 = st.columns(4)

        try:
            total_lines = len(df)
            total_monthly = pd.to_numeric(df.iloc[:, -2], errors='coerce').sum()
            total_settlement = pd.to_numeric(df.iloc[:, -3], errors='coerce').sum()
            total_all = pd.to_numeric(df.iloc[:, -1], errors='coerce').sum()

        except:
            total_lines = 0
            total_monthly = 0
            total_settlement = 0
            total_all = 0

        col1.metric("عدد الخطوط", total_lines)
        col2.metric("إجمالي الرسوم الشهرية", int(total_monthly))
        col3.metric("إجمالي التسويات", int(total_settlement))
        col4.metric("الإجمالي الكلي", int(total_all))

        # 📥 تحميل Excel
        output = BytesIO()
        df.to_excel(output, index=False)

        st.download_button(
            label="📥 تحميل Excel",
            data=output.getvalue(),
            file_name="hawelha_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# الحقوق (زي ما طلبتي)
st.markdown("---")
st.markdown("Developed by **Najat Telecom** © 2026")
