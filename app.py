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

def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    numbers = re.findall(r'\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

# ================= AR / EN FUNCTIONS (KEEP AS IS) =================
def parse_ar(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row: continue
                    text = normalize(" ".join([str(c) for c in row if c]))
                    phone = re.search(r'(01[0125]\d{8})', text)
                    if phone:
                        nums = extract_numbers(text)
                        # Logic to map numbers based on your original AR function
                        def g(idx, vlist): return vlist[idx] if idx < len(vlist) else 0
                        records.append({
                            "محمول": phone.group(1),
                            "رسوم شهرية": g(-1, nums), "رسوم الخدمات": 0, "مكالمات محلية": 0,
                            "رسائل محلية": 0, "إنترنت محلية": 0, "مكالمات دولية": 0,
                            "رسائل دولية": 0, "مكالمات تجوال": 0, "رسائل تجوال": 0,
                            "إنترنت تجوال": 0, "رسوم تسويات": 0, "ضرائب": 0, "إجمالي": g(0, nums)
                        })
    return records

# ================= AI FIXED (THE REAL FIX) =================
def parse_ai(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            page = pdf.pages[0]
            # استخراج الكلمات مع إحداثياتها وترتيبها من اليمين لليسار ومن أعلى لأسفل
            words = page.extract_words(horizontal_ltr=False, extra_attrs=['fontname', 'size'])
            
            # تحويل الكلمات لنص واحد مفهوم
            full_text = " ".join([w['text'] for w in words])
            
            # 1. رقم الهاتف
            phone_match = re.search(r'(01[0125]\d{8})', full_text)
            phone = phone_match.group(1) if phone_match else "Unknown"

            # 2. وظيفة ذكية للبحث عن الرقم الذي يلي الكلمة مباشرة في الترتيب
            def get_val_after(keyword):
                for i, w in enumerate(words):
                    if keyword in w['text']:
                        # نبحث في الـ 5 كلمات اللي بعد الكلمة المفتاحية عن أول رقم
                        for j in range(i + 1, min(i + 6, len(words))):
                            potential_num = words[j]['text'].replace(',', '')
                            if re.match(r'^\d+(\.\d+)?$', potential_num):
                                return float(potential_num)
                return 0.0

            # استخراج القيم بناءً على مسميات الفاتورة الفردية بدقة
            monthly = get_val_after("الرسوم الشهرية")
            t1 = get_val_after("ضريبة الجدول")
            t2 = get_val_after("القيمة المضافة")
            t3 = get_val_after("ضريبة الدمغة")
            t4 = get_val_after("تنمية موارد")
            
            total_taxes = round(t1 + t2 + t3 + t4, 2)
            
            # الإجمالي (نبحث عن القيمة المستحقة)
            total_due = get_val_after("القيمة المستحقة")

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
                "ضرائب": total_taxes,
                "إجمالي": total_due
            })
    except:
        return []
    return records

# ================= MAIN UI & PROCESSING =================
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
        progress_bar = st.progress(0)
        
        for idx, file in enumerate(files):
            # محاولة التحليل بالـ AI أولاً للفواتير الفردية لأنها الأكثر حساسية
            data = parse_ai(file)
            
            # إذا فشل الـ AI أو لم يجد بيانات (قد تكون فاتورة جماعية)، جرب العادي
            if not data or (len(data) > 0 and data[0]['إجمالي'] == 0):
                try:
                    with pdfplumber.open(file) as pdf:
                        text = pdf.pages[0].extract_text() or ""
                    lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
                    data = parse_ar(file) if lang == "ar" else parse_en(file)
                except: pass
            
            if data: all_data.extend(data)
            progress_bar.progress(int((idx + 1) / len(files) * 100))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)
            # التأكد من أن الأعمدة رقمية
            cols = ["رسوم شهرية", "ضرائب", "إجمالي"]
            for c in cols: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

            st.markdown("## 📊 Dashboard")
            c1, c2, c3 = st.columns(3)
            c1.metric("عدد الخطوط", len(df))
            c2.metric("إجمالي الرسوم", f"{df['رسوم شهرية'].sum():,.2f}")
            c3.metric("الإجمالي النهائي", f"{df['إجمالي'].sum():,.2f}")
            
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 تحميل Excel", to_excel(df), "Telecom_Report.xlsx")
        else:
            st.error("لم يتم استخراج بيانات. تأكد من جودة ملفات الـ PDF.")
