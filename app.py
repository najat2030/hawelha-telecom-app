import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os
import gc # لاستدعاء جامع القمامة وتحسين الذاكرة

# ================= CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= MODE =================
# ✔️ Fix: تم تصحيح الرمز من 🇪 إلى 🇪🇬
mode = st.radio(
    "🌐 اختر وضع التحليل",
    ["Auto 🤖", "عربي 🇪", "English 🌍"],
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

# عرض الشعار في أعلى الصفحة - تم تكبير الحجم إلى 80% كما طلبت
if logo:
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 10px;">
        <img src="data:image/png;base64,{logo}" width="80%" style="max-width: 1000px;">
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 🚫🚫 DO NOT MODIFY BELOW THIS LINE 🚫
# ⚠️ هذا الجزء مسؤول عن استخراج البيانات من PDF
# ⚠️ أي تعديل هنا ممكن يكسر:
# - اتجاه البيانات (يمين/شمال)
# - القيم السالبة (-)
# - توزيع الأعمدة
# ⚠️ مسموح فقط التعديل في UI فوق أو تحت
# =========================================================

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

# 🔥 FIX النهائي للسالب (يدعم عربي + إنجليزي)
# ✅ FIX: استبعاد أرقام الهواتف (11 رقم) من القيم المالية لمنع ظهورها في الأعمدة الخاطئة
def extract_numbers(text):
    if not text:
        return []
    text = normalize(str(text))
    
    # (123) → -123
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    # 15- → -15 (العربي)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    # - 15 → -15
    text = re.sub(r'-\s+(\d)', r'-\1', text)
    
    # استخراج جميع الأرقام أولاً
    all_numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    
    # تصفية الأرقام: استبعاد الأرقام التي تتكون من 11 خانة (أرقام محمول)
    financial_values = []
    for n in all_numbers:
        clean_n = n.replace('-', '')
        if len(clean_n) == 11 and '.' not in clean_n:
            continue
        financial_values.append(float(n))
        
    return financial_values

# ================= AR =================
def parse_ar(file):
    records = []
    with pdfplumber.open(file) as pdf:
        # حماية: التأكد من وجود صفحات كافية قبل البدء
        if len(pdf.pages) < 3:
            return records
            
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
                        vals = vals[::-1] # مهم للاتجاه العربي
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
        # حماية: التأكد من وجود صفحات كافية قبل البدء
        if len(pdf.pages) < 3:
            return records

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

# =========================================================
# ✅ UI ONLY BELOW — SAFE TO MODIFY
# =========================================================

# ================= CSS STYLES =================
st.markdown("""
<style>
/* Import Professional Corporate Font (Montserrat) */
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;800&display=swap');
.upload-box {
    background: #f0fdf4;
    border: 2px dashed #10b981;
    border-radius: 15px;
    padding: 1rem;
    text-align: center;
    margin-bottom: 2rem;
}
.kpi {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-top: 4px solid #10b981;
    height: 100%;
}
.kpi h2 {
    color: #059669;
    font-size: 1.8rem;
    margin: 0.5rem 0;
    font-weight: bold;
}
.kpi p {
    color: #6b7280;
    margin: 0;
    font-size: 0.9rem;
    font-weight: 600;
}
.success-box {
    background: #dcfce7;
    border: 1px solid #16a34a;
    color: #166534;
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    margin: 1rem 0;
    font-weight: bold;
}
/* Signature Box Styles - Professional Corporate Look */
.signature-box {
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
    padding: 1.5rem 1rem;
    margin: 0 auto 2rem auto;
    max-width: 600px;
    background-color: #ffffff;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.developer-name-corp {
    font-family: 'Montserrat', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #000000;
    margin: 0;
    letter-spacing: 0.5px;
    text-transform: none;
}
.copyright-text-corp {
    font-family: 'Montserrat', sans-serif;
    font-size: 0.9rem;
    color: #333333;
    margin-top: 0.5rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}
</style>
""", unsafe_allow_html=True)

# ================= SIGNATURE BOX (Under Logo) =================
st.markdown("""
<div class="signature-box">
    <p class="developer-name-corp">Developed by Najat El Bakry</p>
    <p class="copyright-text-corp">© 2026 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)

# ================= INPUT =================
st.markdown('<div class="upload-box"></div>', unsafe_allow_html=True)
file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")

# ================= MAIN =================
if file:
    # ✔️ Improvement: استخدام اسم الملف الأصلي للإكسل (يعمل مع أي اسم ملف)
    # نزيل الامتداد .pdf ونضيف _Converted.xlsx
    safe_filename = file.name.replace('.pdf', '').replace('.PDF', '')
    excel_filename = f"{safe_filename}_Converted.xlsx"

    if st.button("🚀 Start Processing"):
        # تنظيف الذاكرة قبل البدء لتجنب خطأ "Oh no"
        gc.collect()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("⏳ جاري قراءة ملف PDF...")
            progress_bar.progress(10)

            # تحديد اللغة
            if mode == "Auto 🤖":
                with pdfplumber.open(file) as pdf:
                    # قراءة أول صفحة فقط للكشف عن اللغة لتوفير الذاكرة
                    text = pdf.pages[0].extract_text() if len(pdf.pages) > 0 else ""
                lang = "ar" if re.search(r'[\u0600-\u06FF]', text or "") else "en"
            else:
                lang = "ar" if mode == "عربي 🇪" else "en"

            status_text.text(f" تم اكتشاف اللغة: {'العربية' if lang == 'ar' else 'English'}... جاري الاستخراج")
            progress_bar.progress(30)

            # استدعاء دالة الاستخراج المناسبة
            # إعادة فتح الملف لأن المؤشر قد يكون تحرك
            data = parse_ar(file) if lang == "ar" else parse_en(file)
            
            status_text.text("📊 جاري تحويل البيانات إلى جدول...")
            progress_bar.progress(70)

            if data:
                df = pd.DataFrame(data)
                
                del data
                gc.collect()

                status_text.text("✅ اكتملت المعالجة!")
                progress_bar.progress(100)

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
                
                st.markdown(f"""
                <div class="success-box">
                    <h3>🎉 تم التحويل بنجاح</h3>
                </div>
                """, unsafe_allow_html=True)

                st.download_button("📥 تحميل Excel", excel, excel_filename)
                
                del df
                gc.collect()

            else:
                progress_bar.empty()
                status_text.empty()
                st.error("No data found. تأكد أن الملف يحتوي على جداول بيانات من صفحة 3 فما فوق.")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            # عرض خطأ أكثر وضوحاً للمستخدم
            st.error(f"حدث خطأ أثناء المعالجة: {str(e)}")
            st.info("نصيحة: إذا كان الملف كبيراً جداً، حاول تقسيمه إلى أجزاء أصغر.")
