import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom | حوّلها تليكوم", page_icon="📊", layout="wide")

# ================= LOGO =================
def load_logo():
    path = "static/logo.png"
    try:
        if os.path.exists(path):
            with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None
    return None

logo = load_logo()
if logo:
    st.markdown(f'<div style="text-align: center; margin-bottom: 10px;"><img src="data:image/png;base64,{logo}" width="80%" style="max-width: 1000px;"></div>', unsafe_allow_html=True)

# ================= TOOLS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def extract_numbers(text):
    if not text: return []
    try:
        text = normalize(str(text))
        text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
        text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
        numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
        return [float(n) for n in numbers]
    except: return []

# ================= AR =================
def parse_ar(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            # ✅ التعديل الوحيد هنا
            for page in pdf.pages:

                tables = page.extract_tables()
                if not tables: continue

                for table in tables:
                    for i, row in enumerate(table):
                        try:
                            if not row: continue

                            text = normalize(" ".join([str(c) for c in row if c]))
                            phone = re.search(r'(01[0125]\d{8})', text)

                            if phone:
                                p_val = phone.group(1)
                                vals = extract_numbers(text)

                                if len(vals) < 5 and i+1 < len(table):
                                    nxt_text = " ".join([str(c) for c in table[i+1] if c])
                                    vals = extract_numbers(nxt_text)

                                vals = [v for v in vals if str(int(v)) != str(int(p_val))]
                                vals = vals[::-1]

                                def g(idx): return vals[idx] if idx < len(vals) else 0

                                records.append({
                                    "محمول": p_val,
                                    "رسوم شهرية": g(0),
                                    "رسوم الخدمات": g(1),
                                    "مكالمات محلية": g(2),
                                    "رسائل محلية": g(3),
                                    "إنترنت محلية": g(4),
                                    "مكالمات دولية": g(5),
                                    "رسائل دولية": g(6),
                                    "مكالمات تجوال": g(7),
                                    "رسائل تجوال": g(8),
                                    "إنترنت تجوال": g(9),
                                    "رسوم تسويات": g(10),
                                    "ضرائب": g(11),
                                    "إجمالي": g(12),
                                })
                        except:
                            continue
    except:
        pass
    return records

# ================= UI =================
files = st.file_uploader("Upload PDF Files", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")

if files:
    if st.button("🚀 Start Processing"):

        all_data = []
        failed_files = []
        progress = st.progress(0)

        for idx, file in enumerate(files):
            try:
                with pdfplumber.open(file) as pdf:
                    first_text = pdf.pages[0].extract_text() or ""
                    is_ar = bool(re.search(r'[\u0600-\u06FF]', first_text))
                    data = parse_ar(file) if is_ar else []

                if data:
                    all_data.extend(data)
                else:
                    failed_files.append(file.name)

            except:
                failed_files.append(file.name)

            progress.progress((idx + 1) / len(files))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)

            num_cols = ["رسوم شهرية", "رسوم تسويات", "ضرائب", "إجمالي"]
            for c in num_cols:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            st.markdown("## 📊 Dashboard")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("عدد الخطوط", len(df))
            c2.metric("إجمالي الرسوم", f"{df['رسوم شهرية'].sum():,.2f}")
            c3.metric("إجمالي التسويات", f"{df['رسوم تسويات'].sum():,.2f}")
            c4.metric("الإجمالي النهائي", f"{df['إجمالي'].sum():,.2f}")

            st.dataframe(df, use_container_width=True)

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)

            st.download_button("📥 تحميل ملف Excel", excel_buffer.getvalue(), "Hawelha_Report.xlsx")

            if failed_files:
                st.warning(f"⚠️ ملفات لم تكتمل: {', '.join(failed_files)}")
        else:
            st.error("❌ فشل استخراج بيانات من جميع الملفات.")
