import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os

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

# عرض الشعار في أعلى الصفحة إذا كان موجوداً
if logo:
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{logo}" width="250">
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 🚫🚫 DO NOT MODIFY BELOW THIS LINE 🚫🚫
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

                        vals = vals[::-1]  # مهم للاتجاه العربي

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

# =========================================================
# ✅ UI ONLY BELOW — SAFE TO MODIFY
# =========================================================

# ================= CSS STYLES =================
st.markdown("""
<style>
    .upload-box {
        background: #f0fdf4;
        border: 2px dashed #10b981;
        border-radius: 15px;
        padding: 2rem;
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
</style>
""", unsafe_allow_html=True)

# ================= INPUT =================
st.markdown("""
<div class="upload-box">
    <h2>📁 Upload PDF Invoice</h2>
    <p style="color: #666;">Select mode above and upload your file</p>
</div>
""", unsafe_allow_html=True)

file = st.file_uploader("", type=["pdf"])

# ================= MAIN =================
if file:

    if st.button("🚀 Start Processing"):

        with st.spinner("Processing..."):

            if mode == "Auto 🤖":
                with pdfplumber.open(file) as pdf:
                    text = pdf.pages[0].extract_text() or ""
                lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
            else:
                lang = "ar" if mode == "عربي 🇪🇬" else "en"

            data = parse_ar(file) if lang == "ar" else parse_en(file)

            if data:
                df = pd.DataFrame(data)

                # حساب الإجماليات للداشبورد
                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlements = df["رسوم تسويات"].sum()
                total_grand = df["إجمالي"].sum()

                st.markdown("## 📊 Dashboard")

                # عرض 4 مؤشرات أداء رئيسية (KPIs)
                k1, k2, k3, k4 = st.columns(4)

                with k1:
                    st.markdown(f'<div class="kpi"><h2>{total_lines}</h2><p>عدد الخطوط</p></div>', unsafe_allow_html=True)
                
                with k2:
                    st.markdown(f'<div class="kpi"><h2>{total_monthly:,.2f}</h2><p>إجمالي الرسوم الشهرية</p></div>', unsafe_allow_html=True)
                
                with k3:
                    # تلوين التسويات حسب القيمة (سالب/موجب)
                    color = "#ef4444" if total_settlements < 0 else "#059669"
                    st.markdown(f'<div class="kpi" style="border-top-color: {color};"><h2 style="color: {color};">{total_settlements:,.2f}</h2><p>إجمالي التسويات</p></div>', unsafe_allow_html=True)

                with k4:
                    st.markdown(f'<div class="kpi"><h2>{total_grand:,.2f}</h2><p>الإجمالي النهائي</p></div>', unsafe_allow_html=True)

                st.divider()

                st.dataframe(df.head(20), use_container_width=True)

                excel = to_excel(df)

                st.markdown('<div class="success-box">🎉 تم التحويل بنجاح</div>', unsafe_allow_html=True)

                st.download_button("📥 تحميل Excel", excel, "hawelha_invoice_data.xlsx")

            else:
                st.error("No data found")
