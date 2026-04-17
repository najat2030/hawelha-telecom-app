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
    # البحث عن الأرقام التي تحتوي على علامة عشرية فقط لتجنب أرقام الهواتف
    numbers = re.findall(r'\d+\.\d+', text)
    return [float(n) for n in numbers]

# ================= AR / EN FUNCTIONS =================
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
                        # استخراج يدوي للأرقام لضمان الدقة في الفواتير المجمعة
                        vals = re.findall(r'-?\d+(?:\.\d+)?', text)
                        vals = [float(v) for v in vals if v.replace('.','').replace('-','').isdigit()]
                        
                        if i+1 < len(table):
                            nxt_text = " ".join([str(c) for c in table[i+1] if c])
                            nxt = re.findall(r'-?\d+(?:\.\d+)?', nxt_text)
                            nxt = [float(v) for v in nxt if v.replace('.','').replace('-','').isdigit()]
                            if len(nxt) > len(vals): vals = nxt; i += 1
                        
                        # تنظيف رقم الهاتف من القائمة
                        vals = [v for v in vals if str(int(v)) != str(int(phone_val))]
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
                        nxt_text = " ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else ""
                        vals = re.findall(r'-?\d+(?:\.\d+)?', nxt_text)
                        vals = [float(v) for v in vals if str(int(v)) != str(int(phone_val))]
                        
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

# ================= AI FIXED (FINAL REVOLUTION) =================
def parse_ai(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            page = pdf.pages[0]
            # استخراج النص مرتباً حسب الأسطر
            text = page.extract_text()
            if not text: return []
            
            lines = text.split('\n')
            
            # وظيفة للبحث عن أول رقم عشري في سطر يحتوي على كلمة معينة
            def find_in_lines(keyword_list):
                for line in lines:
                    line = normalize(line)
                    if any(k in line for k in keyword_list):
                        nums = re.findall(r'\d+\.\d+', line)
                        if nums: return float(nums[0])
                return 0.0

            # 1. الموبايل
            full_content = normalize(text)
            phone_m = re.search(r'(01[0125]\d{8})', full_content)
            phone = phone_m.group(1) if phone_m else "Unknown"

            # 2. استخراج المبالغ بدقة من الأسطر
            monthly = find_in_lines(["إجمالي الرسوم الشهرية", "الرسوم الشهرية"])
            
            t1 = find_in_lines(["ضريبة الجدول"])
            t2 = find_in_lines(["ضريبة القيمة المضافة"])
            t3 = find_in_lines(["ضريبة الدمغة"])
            t4 = find_in_lines(["رسم تنمية موارد"])
            
            total_taxes = round(t1 + t2 + t3 + t4, 2)
            
            # الإجمالي النهائي
            total_due = find_in_lines(["إجمالي القيمة المستحقة"])

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
            
            # فحص نوع الفاتورة
            try:
                with pdfplumber.open(file) as pdf:
                    first_page = pdf.pages[0].extract_text() or ""
                
                # إذا كانت فاتورة فردية (تحتوي على مسميات معينة) استخدم parse_ai
                if "إجمالي القيمة المستحقة" in first_page or "ضريبة الجدول" in first_page:
                    data = parse_ai(file)
                else:
                    lang = "ar" if re.search(r'[\u0600-\u06FF]', first_page) else "en"
                    data = parse_ar(file) if lang == "ar" else parse_en(file)
                
                if data: all_data.extend(data)
            except:
                pass

            progress.progress(int((idx + 1) / len(files) * 100))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)
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
            st.error("❌ لم يتم العثور على بيانات صحيحة في الملفات.")
