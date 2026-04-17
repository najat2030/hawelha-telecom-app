import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom", page_icon="📊", layout="wide")

# ================= LOGO =================
def load_logo():
    path = "static/logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return None

logo = load_logo()
if logo:
    st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo}" width="80%"></div>', unsafe_allow_html=True)

# ================= TOOLS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def fix_phone(phone):
    phone = str(phone)
    if len(phone) == 10 and phone.startswith("1"): return "0" + phone
    return phone

# ================= AI FIXED (THE ULTIMATE VERSION) =================
def parse_ai(file):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            page = pdf.pages[0]
            words = page.extract_words() # استخراج كل كلمة بمكانها
            
            # تحويل كل الكلمات لنص واحد للبحث عن رقم الموبايل
            full_text = " ".join([w['text'] for w in words])
            phone_m = re.search(r'(01[0125]\d{8})', full_text)
            phone = phone_m.group(1) if phone_m else "Unknown"

            # دالة سحرية: تبحث عن كلمة وتأخذ أول رقم "عشري" يظهر بعدها في ترتيب الكلمات
            def find_nearest_amount(keywords):
                for i, w in enumerate(words):
                    if any(k in w['text'] for k in keywords):
                        # ابحث في الـ 15 كلمة التالية عن رقم فيه نقطة عشري
                        for j in range(i + 1, min(i + 16, len(words))):
                            potential = words[j]['text'].replace(',', '')
                            if re.match(r'^\d+\.\d+$', potential):
                                return float(potential)
                return 0.0

            # استخراج القيم بناءً على المسميات في صورتك
            monthly = find_nearest_amount(["الشهرية"])
            t1 = find_nearest_amount(["الجدول"])
            t2 = find_nearest_amount(["المضافة"])
            t3 = find_nearest_amount(["الدمغة"])
            t4 = find_nearest_amount(["تنمية"])
            
            total_taxes = round(t1 + t2 + t3 + t4, 2)
            total_due = find_nearest_amount(["المستحقة"])

            # إذا فشلت الطريقة السابقة، نحاول البحث عن مبالغ في آخر الصفحة
            if total_due == 0:
                all_amounts = [float(w['text'].replace(',','')) for w in words if re.match(r'^\d+\.\d+$', w['text'].replace(',',''))]
                if all_amounts: total_due = all_amounts[-1]

            records.append({
                "محمول": phone, "رسوم شهرية": monthly, "رسوم الخدمات": 0, "مكالمات محلية": 0,
                "رسائل محلية": 0, "إنترنت محلية": 0, "مكالمات دولية": 0, "رسائل دولية": 0,
                "مكالمات تجوال": 0, "رسائل تجوال": 0, "إنترنت تجوال": 0, "رسوم تسويات": 0,
                "ضرائب": total_taxes, "إجمالي": total_due
            })
    except: return []
    return records

# ================= AR / EN (REDUCED FOR STABILITY) =================
def parse_legacy(file, lang):
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages[2:]:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        row_str = " ".join([str(c) for c in row if c])
                        phone = re.search(r'(01[0125]\d{8})', row_str)
                        if phone:
                            nums = re.findall(r'-?\d+(?:\.\d+)?', row_str)
                            nums = [float(n) for n in nums if n.count('.') <= 1]
                            # هنا نضع منطق التوزيع البسيط
                            records.append({
                                "محمول": phone.group(1), "رسوم شهرية": nums[-1] if nums else 0,
                                "ضرائب": 0, "إجمالي": nums[0] if nums else 0
                            })
    except: pass
    return records

# ================= MAIN ENGINE =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w: df.to_excel(w, index=False)
    return out.getvalue()

files = st.file_uploader("Upload PDF Files", type=["pdf"], accept_multiple_files=True)

if files and st.button("🚀 Start Processing"):
    all_data = []
    progress = st.progress(0)
    
    for idx, file in enumerate(files):
        # المبدأ: جرب الـ AI أولاً (للفواتير الفردية)
        data = parse_ai(file)
        
        # إذا كانت النتائج كلها أصفار، جرب الطريقة التقليدية (للفواتير المجمعة)
        if not data or (data[0]['إجمالي'] == 0 and data[0]['رسوم شهرية'] == 0):
            with pdfplumber.open(file) as pdf:
                text = pdf.pages[0].extract_text() or ""
            lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
            data = parse_legacy(file, lang)
            
        if data: all_data.extend(data)
        progress.progress((idx + 1) / len(files))

    if all_data:
        df = pd.DataFrame(all_data).fillna(0)
        st.markdown("### 📊 النتائج")
        st.dataframe(df)
        st.download_button("📥 تحميل ملف Excel", to_excel(df), "Telecom_Report.xlsx")
    else:
        st.error("❌ فشل استخراج أي بيانات. الملفات قد تكون صوراً (Scanned) وليست نصوصاً.")
