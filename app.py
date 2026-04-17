import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# 1. الإعدادات الأساسية
st.set_page_config(page_title="Hawelha Telecom | حوّلها تليكوم", page_icon="📊", layout="wide")

# 2. وضع التحليل
mode = st.radio("🌐 اختر وضع التحليل", ["Auto 🤖", "عربي 🇪🇬", "English 🌍"], horizontal=True)

# 3. اللوجو (مع حماية المسار)
def load_logo():
    path = "static/logo.png"
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        return None
    return None

logo = load_logo()
if logo:
    st.markdown(f'<div style="text-align: center; margin-bottom: 10px;"><img src="data:image/png;base64,{logo}" width="80%" style="max-width: 1000px;"></div>', unsafe_allow_html=True)
else:
    st.markdown('<h1 style="text-align: center; color: #1E88E5;">Hawelha Telecom | حوّلها تليكوم</h1>', unsafe_allow_html=True)

# 4. أدوات المعالجة الأصلية
def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

# 5. منطق العربي (الأصلي)
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
                        p_val = phone.group(1)
                        vals = extract_numbers(text)
                        if i+1 < len(table):
                            nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                            if len(nxt) > len(vals): vals = nxt; i += 1
                        vals = [v for v in vals if str(int(v)) != str(int(p_val))]
                        vals = vals[::-1]
                        def g(idx): return vals[idx] if idx < len(vals) else 0
                        records.append({
                            "محمول": p_val, "رسوم شهرية": g(0), "رسوم الخدمات": g(1),
                            "مكالمات محلية": g(2), "رسائل محلية": g(3), "إنترنت محلية": g(4),
                            "مكالمات دولية": g(5), "رسائل دولية": g(6), "مكالمات تجوال": g(7),
                            "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10),
                            "ضرائب": g(11), "إجمالي": g(12),
                        })
                    i += 1
    return records

# 6. منطق الإنجليزي (الأصلي)
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
                        p_val = phone.group(1)
                        nxt_text = " ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else ""
                        vals = extract_numbers(nxt_text)
                        vals = [v for v in vals if str(int(v)) != str(int(p_val))]
                        records.append({
                            "محمول": p_val, "رسوم شهرية": vals[0] if len(vals)>0 else 0,
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

# 7. الواجهة النهائية
files = st.file_uploader("ارفع ملفات PDF", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")

if files:
    if st.button("🚀 ابدأ المعالجة"):
        all_data = []
        progress = st.progress(0)
        
        for idx, file in enumerate(files):
            try:
                with pdfplumber.open(file) as pdf:
                    first_text = pdf.pages[0].extract_text() or ""
                    
                if mode == "Auto 🤖":
                    lang = "ar" if re.search(r'[\u0600-\u06FF]', first_text) else "en"
                else:
                    lang = "ar" if mode == "عربي 🇪🇬" else "en"
                
                data = parse_ar(file) if lang == "ar" else parse_en(file)
                if data: all_data.extend(data)
            except:
                continue
            
            progress.progress((idx + 1) / len(files))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)
            
            # DASHBOARD
            st.markdown("## 📊 Dashboard")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("عدد الخطوط", len(df))
            k2.metric("إجمالي الرسوم الشهرية", f"{df['رسوم شهرية'].sum():,.2f}")
            k3.metric("إجمالي التسويات", f"{df['رسوم تسويات'].sum():,.2f}")
            k4.metric("الإجمالي النهائي", f"{df['إجمالي'].sum():,.2f}")

            st.dataframe(df, use_container_width=True)

            # EXCEL DOWNLOAD
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine="openpyxl") as w:
                df.to_excel(w, index=False)
            st.success("🎉 تم التحويل بنجاح")
            st.download_button("📥 تحميل Excel", out.getvalue(), "Hawelha_Report.xlsx")
        else:
            st.error("لم يتم استخراج بيانات. تأكد من جودة الملفات.")
