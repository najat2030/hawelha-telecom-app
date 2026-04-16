import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os
import gc

# ================= CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= MODE =================
mode = st.radio(
    "🌐 اختر وضع التحليل",
    ["Auto 🤖", "عربي 🇪🇬", "English 🌍"],
    horizontal=True
)

# ================= LOGO =================
def load_logo():
    path = "static/logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo = load_logo()

if logo:
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 10px;">
        <img src="data:image/png;base64,{logo}" width="80%" style="max-width: 1000px;">
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 🚫🚫 DO NOT MODIFY BELOW THIS LINE 🚫
# =========================================================

def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def extract_numbers(text):
    if not text:
        return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

# ================= AR =================
def parse_ar(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue
                    text = normalize(" ".join([str(c) for c in row if c]))
                    phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        phone = phone.group(1)
                        vals = extract_numbers(text)
                        if i+1 < len(table):
                            nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                            if len(nxt) > len(vals):
                                vals = nxt
                                i += 1
                        vals = vals[::-1]
                        def g(i): return vals[i] if i < len(vals) else 0
                        records.append({
                            "محمول": phone,
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
                    i += 1
    return records

# ================= EN =================
def parse_en(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue
                    text = " ".join([str(c) for c in row])
                    phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        phone = phone.group(1)
                        vals = extract_numbers(" ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else "")
                        records.append({
                            "محمول": phone,
                            "رسوم شهرية": vals[0] if len(vals)>0 else 0,
                            "رسوم الخدمات": vals[1] if len(vals)>1 else 0,
                            "مكالمات محلية": vals[2] if len(vals)>2 else 0,
                            "رسائل محلية": vals[3] if len(vals)>3 else 0,
                            "إنترنت محلية": vals[4] if len(vals)>4 else 0,
                            "مكالمات دولية": vals[5] if len(vals)>5 else 0,
                            "رسائل دولية": vals[6] if len(vals)>6 else 0,
                            "مكالمات تجوال": vals[7] if len(vals)>7 else 0,
                            "رسائل تجوال": vals[8] if len(vals)>8 else 0,
                            "إنترنت تجوال": vals[9] if len(vals)>9 else 0,
                            "رسوم تسويات": vals[10] if len(vals)>10 else 0,
                            "ضرائب": vals[11] if len(vals)>11 else 0,
                            "إجمالي": vals[-1] if vals else 0
                        })
                        i += 2
                        continue
                    i += 1
    return records

# ================= EXCEL =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= UI =================
st.markdown('<div class="upload-box"></div>', unsafe_allow_html=True)

files = st.file_uploader(
    "Upload PDF Files",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# ================= MAIN =================
if files:

    if st.button("🚀 Start Processing"):

        progress_bar = st.progress(0)
        status_text = st.empty()

        all_data = []
        failed_files = []

        try:
            total_files = len(files)

            for idx, file in enumerate(files):

                try:
                    status_text.text(f"📄 Processing: {file.name}")
                    progress_bar.progress(int((idx / total_files) * 100))

                    if mode == "Auto 🤖":
                        with pdfplumber.open(file) as pdf:
                            text = pdf.pages[0].extract_text() or ""
                        lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
                    else:
                        lang = "ar" if mode == "عربي 🇪🇬" else "en"

                    for attempt in range(3):
                        try:
                            data = parse_ar(file) if lang == "ar" else parse_en(file)
                            break
                        except:
                            if attempt == 2:
                                raise

                    if data:
                        all_data.extend(data)

                except Exception:
                    failed_files.append(file.name)
                    continue

                gc.collect()

            progress_bar.progress(100)
            status_text.text("✅ اكتملت المعالجة!")

            if all_data:

                df = pd.DataFrame(all_data)

                # ================= FIX المشكلة =================
                def clean_number(x):
                    x = str(x).replace(".0", "").strip()
                    if x.startswith("0"):
                        x = x[1:]
                    return x

                mobile_clean = df["محمول"].astype(str).apply(clean_number)

                for col in df.columns:
                    if col != "محمول":
                        df[col] = df[col].apply(
                            lambda x: 0 if clean_number(x) in mobile_clean.values else x
                        )

                # ================= DASHBOARD =================
                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlements = df["رسوم تسويات"].sum()
                total_grand = df["إجمالي"].sum()

                st.markdown("## 📊 Dashboard")

                k1, k2, k3, k4 = st.columns(4)

                with k1:
                    st.markdown(f'<div class="kpi"><h2>{total_lines}</h2><p>عدد الخطوط</p></div>', unsafe_allow_html=True)
                with k2:
                    st.markdown(f'<div class="kpi"><h2>{total_monthly:,.2f}</h2><p>إجمالي الرسوم الشهرية</p></div>', unsafe_allow_html=True)
                with k3:
                    color = "#ef4444" if total_settlements < 0 else "#059669"
                    st.markdown(f'<div class="kpi" style="border-top-color: {color};"><h2 style="color: {color};">{total_settlements:,.2f}</h2><p>إجمالي التسويات</p></div>', unsafe_allow_html=True)
                with k4:
                    st.markdown(f'<div class="kpi"><h2>{total_grand:,.2f}</h2><p>الإجمالي النهائي</p></div>', unsafe_allow_html=True)

                st.divider()

                st.dataframe(df.head(20), use_container_width=True)

                excel = to_excel(df)

                st.markdown('<div class="success-box">🎉 تم التحويل بنجاح</div>', unsafe_allow_html=True)

                st.download_button("📥 تحميل Excel", excel, "hawelha_all_files.xlsx")

                if failed_files:
                    st.warning(f"⚠️ فواتير فشلت: {len(failed_files)}")
                    st.write(failed_files)

            else:
                st.error("No data extracted")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"حدث خطأ: {str(e)}")

# ================= SIGNATURE =================
st.markdown("""
<div style="text-align:center; margin-top:40px; font-weight:bold;">
Developed by Najat El Bakry © 2026
</div>
""", unsafe_allow_html=True)
