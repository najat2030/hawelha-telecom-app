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

# ================= TOOLS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def fix_phone(phone):
    phone = str(phone)
    if len(phone) == 10 and phone.startswith("1"):
        return "0" + phone
    return phone

# ================= AR / EN (KEEPING ORIGINAL LOGIC) =================
def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

def clean_numbers(vals, phone):
    try:
        phone_int = str(int(phone))
        return [v for v in vals if str(int(v)) != phone_int]
    except: return vals

def parse_ar(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row: i += 1; continue
                    text = normalize(" ".join([str(c) for c in row if c]))
                    phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        phone_val = phone.group(1)
                        vals = extract_numbers(text)
                        if i+1 < len(table):
                            nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                            if len(nxt) > len(vals): vals = nxt; i += 1
                        vals = clean_numbers(vals, phone_val)
                        vals = vals[::-1]
                        def g(idx): return vals[idx] if idx < len(vals) else 0
                        records.append({
                            "محمول": phone_val, "رسوم شهرية": g(0), "رسوم الخدمات": g(1),
                            "مكالمات محلية": g(2), "رسائل محلية": g(3), "إنترنت محلية": g(4),
                            "مكالمات دولية": g(5), "رسائل دولية": g(6), "مكالمات تجوال": g(7),
                            "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10),
                            "ضرائب": g(11), "إجمالي": g(12),
                        })
                    i += 1
    return records

def parse_en(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row: i += 1; continue
                    text = " ".join([str(c) for c in row])
                    phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        phone_val = phone.group(1)
                        vals = extract_numbers(" ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else "")
                        vals = clean_numbers(vals, phone_val)
                        records.append({
                            "محمول": phone_val, "رسوم شهرية": vals[0] if len(vals)>0 else 0,
                            "رسوم الخدمات": vals[1] if len(vals)>1 else 0, "مكالمات محلية": vals[2] if len(vals)>2 else 0,
                            "رسائل محلية": vals[3] if len(vals)>3 else 0, "إنترنت محلية": vals[4] if len(vals)>4 else 0,
                            "مكالمات دولية": vals[5] if len(vals)>5 else 0, "رسائل دولية": vals[6] if len(vals)>6 else 0,
                            "مكالمات تجوال": vals[7] if len(vals)>7 else 0, "رسائل تجوال": vals[8] if len(vals)>8 else 0,
                            "إنترنت تجوال": vals[9] if len(vals)>9 else 0, "رسوم تسويات": vals[10] if len(vals)>10 else 0,
                            "ضرائب": vals[11] if len(vals)>11 else 0, "إجمالي": vals[-1] if vals else 0
                        })
                        i += 2; continue
                    i += 1
    return records

# ================= AI FIXED (THE FINAL SOLUTION) =================
def parse_ai(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            page = pdf.pages[0]
            # الطريقة السحرية: استخراج الكلمات وترتيبها يدوياً لتجاوز التشفير
            words = page.extract_words(horizontal_ltr=False)
            if not words: return []
            
            # إعادة بناء النص من الكلمات المبعثرة
            full_text = " ".join([w['text'] for w in words])
            full_text = normalize(full_text)

            def find_val(keyword):
                # البحث عن الكلمة ثم الرقم اللي بعدها مباشرة في قائمة الكلمات
                for idx, w in enumerate(words):
                    if keyword in w['text']:
                        # فحص الكلمات الـ 10 التالية للكلمة المفتاحية
                        for j in range(idx + 1, min(idx + 10, len(words))):
                            txt = words[j]['text'].replace(',', '')
                            if re.match(r'^-?\d+(?:\.\d+)?$', txt):
                                return float(txt)
                return 0.0

            # 1. الموبايل
            phone_m = re.search(r'(01[0125]\d{8})', full_text)
            phone = phone_m.group(1) if phone_m else "Unknown"

            # 2. استخراج المبالغ
            monthly = find_val("الرسوم الشهرية")
            t_table = find_val("ضريبة الجدول")
            t_vat = find_val("القيمة المضافة")
            t_stamp = find_val("ضريبة الدمغة")
            t_dev = find_val("تنمية موارد")
            
            total_taxes = round(t_table + t_vat + t_stamp + t_dev, 2)
            total_due = find_val("القيمة المستحقة")

            records.append({
                "محمول": phone, "رسوم شهرية": monthly, "رسوم الخدمات": 0, "مكالمات محلية": 0,
                "رسائل محلية": 0, "إنترنت محلية": 0, "مكالمات دولية": 0, "رسائل دولية": 0,
                "مكالمات تجوال": 0, "رسائل تجوال": 0, "إنترنت تجوال": 0, "رسوم تسويات": 0,
                "ضرائب": total_taxes, "إجمالي": total_due
            })
    except: return []
    return records

# ================= UI & ENGINE =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

files = st.file_uploader("Upload PDF Files", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")

if files:
    if st.button("🚀 Start Processing"):
        all_data = []
        progress = st.progress(0)
        status = st.empty()

        for idx, file in enumerate(files):
            status.text(f"📄 Processing: {file.name}")
            
            # محاولة قراءة الفاتورة الفردية أولاً لأنها الأكثر تعقيداً
            data = parse_ai(file)
            
            # إذا لم يجد بيانات (قد تكون فاتورة مجمعة)، جرب الطرق التقليدية
            if not data or (len(data) > 0 and data[0]['إجمالي'] == 0):
                try:
                    with pdfplumber.open(file) as pdf:
                        check_text = pdf.pages[0].extract_text() or ""
                    lang = "ar" if re.search(r'[\u0600-\u06FF]', check_text) else "en"
                    data = parse_ar(file) if lang == "ar" else parse_en(file)
                except: pass

            if data: all_data.extend(data)
            progress.progress(int((idx + 1) / len(files) * 100))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)
            # تحويل الأعمدة لرقمية لضمان عمل الداشبورد
            numeric_cols = ["رسوم شهرية", "ضرائب", "إجمالي"]
            for col in numeric_cols: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            st.markdown("## 📊 Dashboard")
            k1, k2, k3 = st.columns(3)
            k1.metric("عدد الخطوط", len(df))
            k2.metric("إجمالي الرسوم", f"{df['رسوم شهرية'].sum():,.2f}")
            k3.metric("الإجمالي النهائي", f"{df['إجمالي'].sum():,.2f}")
            
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 تحميل Excel", to_excel(df), "Telecom_Report.xlsx")
        else:
            st.error("❌ لم يتم استخراج بيانات. الفاتورة الفردية قد تكون محمية بطبقة إضافية.")
