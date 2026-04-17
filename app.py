import streamlit as st
import pdfplumber
import pandas as pd
import re
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
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

# ================= AR TABLE =================
def parse_ar(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                for row in table:
                    text = normalize(" ".join([str(c) for c in row if c]))
                    phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        vals = extract_numbers(text)
                        vals = [v for v in vals if str(int(v)) != phone.group(1)]

                        def g(i): return vals[i] if i < len(vals) else 0

                        records.append({
                            "محمول": phone.group(1),
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
                            "إجمالي": g(-1),
                        })
    return records

# ================= SMART (الفواتير الفردي) =================
def parse_smart_text(file):
    records = []

    with pdfplumber.open(file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() or ""

    full_text = normalize(full_text)

    phone_match = re.search(r'(01[0125]\d{8})', full_text)
    if not phone_match:
        return []

    phone = phone_match.group(1)

    def find_value(label):
        pattern = rf"{label}.*?(\d+\.\d+)"
        match = re.search(pattern, full_text)
        return float(match.group(1)) if match else 0

    records.append({
        "محمول": phone,
        "رسوم شهرية": find_value("الرسوم الشهرية"),
        "رسوم الخدمات": find_value("رسوم الخدمات"),
        "مكالمات محلية": find_value("مكالمات"),
        "رسائل محلية": find_value("رسائل"),
        "إنترنت محلية": find_value("الإنترنت"),
        "مكالمات دولية": find_value("دولي"),
        "رسائل دولية": find_value("رسائل دولية"),
        "مكالمات تجوال": find_value("التجوال"),
        "رسائل تجوال": find_value("رسائل تجوال"),
        "إنترنت تجوال": find_value("إنترنت تجوال"),
        "رسوم تسويات": find_value("تسوية"),
        "ضرائب": find_value("ضريبة"),
        "إجمالي": find_value("إجمالي")
    })

    return records

# ================= PROCESS =================
def process_file(file):
    try:
        data = parse_ar(file)

        # لو الجدول فشل → نستخدم الذكي
        if not data or all(v == 0 for v in data[0].values() if isinstance(v, (int, float))):
            data = parse_smart_text(file)

        return data
    except:
        return []

# ================= EXCEL =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= UI =================
files = st.file_uploader("رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 Start Processing"):

        progress = st.progress(0)
        all_data = []

        for i, f in enumerate(files):
            result = process_file(f)
            if result:
                all_data.extend(result)

            progress.progress((i+1)/len(files))

        if all_data:
            df = pd.DataFrame(all_data)

            st.dataframe(df.head(20))

            excel = to_excel(df)

            st.success("🎉 تم التحويل بنجاح")
            st.download_button("📥 تحميل Excel", excel, "hawelha.xlsx")

        else:
            st.error("❌ لم يتم استخراج بيانات")

# ================= SIGNATURE =================
st.markdown("""
<hr>
<div style="text-align:center; color:gray;">
Made by ❤️ نوجا
</div>
""", unsafe_allow_html=True)
