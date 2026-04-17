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
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

def clean_numbers(vals, phone):
    phone_int = str(int(phone))
    return [v for v in vals if str(int(v)) != phone_int]

def fix_phone(phone):
    phone = str(phone)
    if len(phone) == 10 and phone.startswith("1"):
        return "0" + phone
    return phone

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

                        vals = clean_numbers(vals, phone)
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

                        vals = clean_numbers(vals, phone)

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

# ================= AI FIXED =================
def parse_ai(file):
    records = []

    try:
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += normalize(page.extract_text() or "")

        phone_match = re.search(r'(01[0125]\d{8}|\b1[0125]\d{8}\b)', text)
        if not phone_match:
            return []

        phone = fix_phone(phone_match.group(1))

        def get(pattern):
            match = re.search(pattern, text)
            return float(match.group(1)) if match else 0

        # ✅ الرسوم الشهرية
        monthly = get(r'إجمالي الرسوم الشهرية.*?(\d+\.\d+)')

        # ✅ الضرائب (جمع)
        tax1 = get(r'ضريبة الجدول.*?(\d+\.\d+)')
        tax2 = get(r'ضريبة القيمة المضافة.*?(\d+\.\d+)')
        tax3 = get(r'ضريبة الدمغة.*?(\d+\.\d+)')
        tax4 = get(r'تنمية موارد الدولة.*?(\d+\.\d+)')

        taxes = tax1 + tax2 + tax3 + tax4

        # ✅ الإجمالي
        total = get(r'إجمالي القيمة المستحقة.*?(\d+\.\d+)')

        records.append({
            "محمول": phone,
            "رسوم شهرية": monthly,
            "رسوم الخدمات": 0,
            "مكالمات محلية": 0,
            "رسائل محلية": 0,
            "إنترنت محلية": 0,
            "مكالمات دولية": 0,
            "رسائل دولية": 0,
            "مكالمات تجوال": 0,
            "رسائل تجوال": 0,
            "إنترنت تجوال": 0,
            "رسوم تسويات": 0,
            "ضرائب": round(taxes, 2),
            "إجمالي": total
        })

    except:
        return []

    return records

# ================= EXCEL =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= UI =================
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

                data = []

                try:
                    data = parse_ar(file) if lang == "ar" else parse_en(file)
                except:
                    data = []

                if not data:
                    data = parse_ai(file)

                if data:
                    all_data.extend(data)

            except:
                failed_files.append(file.name)
                continue

            gc.collect()

        progress_bar.progress(100)
        status_text.text("✅ اكتملت المعالجة!")

        if all_data:

            df = pd.DataFrame(all_data)

            total_lines = len(df)
            total_monthly = df["رسوم شهرية"].sum()
            total_settlements = df["رسوم تسويات"].sum()
            total_grand = df["إجمالي"].sum()

            st.markdown("## 📊 Dashboard")

            k1, k2, k3, k4 = st.columns(4)

            with k1:
                st.metric("عدد الخطوط", total_lines)
            with k2:
                st.metric("إجمالي الرسوم الشهرية", f"{total_monthly:,.2f}")
            with k3:
                st.metric("إجمالي التسويات", f"{total_settlements:,.2f}")
            with k4:
                st.metric("الإجمالي النهائي", f"{total_grand:,.2f}")

            st.dataframe(df.head(20), use_container_width=True)

            excel = to_excel(df)

            st.success("🎉 تم التحويل بنجاح")
            st.download_button("📥 تحميل Excel", excel, "hawelha_all_files.xlsx")

            if failed_files:
                st.warning(f"⚠️ فواتير فشلت: {len(failed_files)}")
                st.write(failed_files)

        else:
            st.error("No data extracted")
