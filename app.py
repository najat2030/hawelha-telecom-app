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

if logo:
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 10px;">
        <img src="image/png;base64,{logo}" width="80%" style="max-width: 1000px;">
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 🚫 DO NOT MODIFY BELOW THIS LINE (LOGIC & DATA)
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
    
    financial_values = []
    for n in numbers:
        clean_n = n.replace('-', '')
        if len(clean_n) == 11 and '.' not in clean_n:
            continue
        financial_values.append(float(n))
        
    return financial_values

# ================= AR =================
def parse_ar(file):
    records = []
    with pdfplumber.open(file) as pdf:
        if len(pdf.pages) < 3: 
            return records
        
        for page in pdf.pages[2:]:
            # ✅ FIX: تخطي الصفحات التحليلية/البيانية
            page_text = page.extract_text() or ""
            skip_keywords = ["تحليل", "خطط", "أسعار", "رسم بياني", "الدقائق", "المكالمات داخل الشبكة", "قيمة الفاتورة في آخر ثلاث شهور", "ملخص", "تقرير"]
            if any(keyword in page_text for keyword in skip_keywords):
                continue

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
                        phone_num = phone.group(1)
                        vals = extract_numbers(text)
                        if i+1 < len(table):
                            nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                            if len(nxt) > len(vals):
                                vals = nxt
                                i += 1
                        vals = vals[::-1]
                        def g(i): return vals[i] if i < len(vals) else 0
                        records.append({
                            "محمول": phone_num,
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
        if len(pdf.pages) < 3: 
            return records
        
        for page in pdf.pages[2:]:
            # ✅ FIX: تخطي الصفحات التحليلية/البيانية
            page_text = page.extract_text() or ""
            skip_keywords = ["Analysis", "Plan", "Price", "Chart", "Minutes", "Calls within network", "Invoice value last three months", "Summary", "Report"]
            if any(keyword in page_text for keyword in skip_keywords):
                continue

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
                        phone_num = phone.group(1)
                        vals = extract_numbers(" ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else "")
                        records.append({
                            "محمول": phone_num,
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
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;800&display=swap');
    .upload-box {
        background: #f0fdf4;
        border: 2px dashed #10b981;
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 2rem;
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
    .signature-box {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid #e5e7eb;
    }
    .developer-name {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.4rem;
        font-weight: 800;
        color: #000000;
        margin: 0;
    }
    .copyright-text {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.9rem;
        color: #6b7280;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ================= INPUT =================
st.markdown('<div class="upload-box"><h3>📁 Upload Multiple PDF Invoices</h3></div>', unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Choose PDF files",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# ================= SIGNATURE & COPYRIGHT =================
st.markdown("""
<div class="signature-box">
    <p class="developer-name">Developed by Najat El Bakry</p>
    <p class="copyright-text">© 2026 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)

# ================= MAIN =================
if uploaded_files:

    excel_filename = f"Hawelha_Combined_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    if st.button("🚀 Start Processing"):

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            all_data = []
            total_files = len(uploaded_files)

            for idx, file in enumerate(uploaded_files):
                progress_percent = int(((idx + 1) / total_files) * 100)
                status_text.text(f"⏳ جاري معالجة الملف {idx+1} من {total_files}: {file.name}...")
                progress_bar.progress(progress_percent)

                try:
                    if mode == "Auto 🤖":
                        with pdfplumber.open(file) as pdf:
                            text = pdf.pages[0].extract_text() if len(pdf.pages) > 0 else ""
                        lang = "ar" if re.search(r'[\u0600-\u06FF]', text or "") else "en"
                    else:
                        lang = "ar" if mode == "عربي 🇪" else "en"

                    data = parse_ar(file) if lang == "ar" else parse_en(file)

                    # ✅ FIX: Corrected syntax here
                    if 
                        all_data.extend(data)
                        
                    # ✅ MEMORY OPTIMIZATION: Force garbage collection after each file
                    del data
                    gc.collect()

                except Exception as e:
                    st.warning(f"تم تخطي ملف {file.name} بسبب خطأ: {str(e)}")
                    continue

            # ✅ FIX: Corrected syntax here
            if all_
                # تحويل القائمة إلى DataFrame مرة واحدة في النهاية
                df = pd.DataFrame(all_data)
                
                # تنظيف الذاكرة من القائمة الأصلية
                del all_data
                gc.collect()

                # تنظيف إضافي للبيانات (منع رقم الموبايل في الأعمدة الرقمية)
                for col in df.columns:
                    if col != "محمول":
                        mask = df[col].astype(str).str.match(r'^01[0125]\d{8}$')
                        df.loc[mask, col] = 0

                status_text.text("✅ اكتملت المعالجة!")
                progress_bar.progress(100)

                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlements = df["رسوم تسويات"].sum()
                total_grand = df["إجمالي"].sum()

                st.markdown("## 📊 Dashboard (Combined Results)")

                k1, k2, k3, k4 = st.columns(4)

                with k1:
                    st.metric("عدد الخطوط", total_lines)

                with k2:
                    st.metric("إجمالي الرسوم الشهرية", f"{total_monthly:,.2f}")

                with k3:
                    st.metric("إجمالي التسويات", f"{total_settlements:,.2f}")

                with k4:
                    st.metric("الإجمالي النهائي", f"{total_grand:,.2f}")

                st.divider()
                
                # ✅ PERFORMANCE: عرض عدد أقل من الصفوف لتوفير ذاكرة المتصفح
                st.dataframe(df.head(10), use_container_width=True)

                excel = to_excel(df)
                
                # تنظيف الذاكرة بعد إنشاء الإكسل
                del df
                gc.collect()

                st.markdown("""
                <div class="success-box">
                    <h3>🎉 تم دمج وتحويل جميع الملفات بنجاح!</h3>
                    <p>اضغط على الزر أدناه لتحميل ملف Excel الموحد.</p>
                </div>
                """, unsafe_allow_html=True)

                st.download_button("📥 تحميل Excel الموحد", excel, excel_filename)

            else:
                st.error("No data found in any of the uploaded files.")

        except Exception as e:
            st.error(f"حدث خطأ أثناء المعالجة: {str(e)}")
            st.info("نصيحة: إذا كانت الملفات كبيرة جداً، حاول رفع عدد أقل من الملفات في المرة الواحدة لتجنب حدود ذاكرة السيرفر.")
