import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import os
import gc

# ================= CONFIG & STYLE =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide", page_icon="📊")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap'); 
.stApp { background-color: #f8f9fa; font-family: 'Tajawal', sans-serif; } 
.login-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); text-align: center; max-width: 400px; margin: auto; }
.royal-green-box { background-color: #1a7e43; color: white; padding: 8px 16px; border-radius: 50px; display: flex; align-items: center; gap: 8px; width: fit-content; margin-left: auto; }
.metric-card { background: white; padding: 15px; border-radius: 12px; border-right: 5px solid #1a7e43; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.stProgress > div > div > div > div { background-color: #daa520 !important; }
</style>
""", unsafe_allow_html=True)

# ================= USERS =================
def load_users():
    try:
        df = pd.read_excel("users.xlsx")
        return {str(r["Username"]).strip(): str(r["Password"]).strip() for _, r in df.iterrows()}
    except: return {"admin": "123"} # افتراضي لو الملف مش موجود

users = load_users()

# ================= SESSION =================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="login-card"><h2>🔐 دخول</h2></div>', unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("تسجيل الدخول"):
            if u in users and users[u] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else: st.error("خطأ!")
    st.stop()

# ================= LOGIC =================
def normalize(t):
    return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")

def extract_numbers(text):
    if not text: return []
    text = normalize(str(text))
    # تعديل مهم جداً لضمان فصل السالب عن الرقم السابق
    text = re.sub(r'(\d)-', r'\1 -', text)
    return [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', text)]

def parse_file(file, force_lang=None):
    records = []
    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            # كشف اللغة للملف ده تحديداً
            first_page = pdf.pages[0].extract_text() or ""
            is_arabic = re.search(r'[\u0600-\u06FF]', first_page) if not force_lang else (force_lang == "ar")
            
            for page in pdf.pages[2:]: # تخطي أول صفحتين
                tables = page.extract_tables()
                for table in tables or []:
                    for i, row in enumerate(table):
                        if not row: continue
                        text = normalize(" ".join([str(c) for c in row if c]))
                        phone = re.search(r'(01[0125]\d{8})', text)
                        
                        if phone:
                            p = phone.group(1)
                            vals = extract_numbers(text)
                            
                            # محاولة سحب السطر التكميلي لو موجود
                            if i + 1 < len(table):
                                nxt_text = " ".join([str(c) for c in table[i+1] if c])
                                if not re.search(r'(01[0125]\d{8})', nxt_text):
                                    nxt_vals = extract_numbers(nxt_text)
                                    if len(nxt_vals) > len(vals):
                                        vals = nxt_vals
                            
                            # تنظيف القيم من رقم الموبايل نفسه
                            vals = [v for v in vals if str(int(v)) != str(int(p))]
                            
                            # العكس فقط لو الملف عربي (لأن العربي بيتقرأ من اليمين في الـ PDF)
                            if is_arabic:
                                vals = vals[::-1]
                            
                            def g(idx): return vals[idx] if idx < len(vals) else 0
                            
                            records.append({
                                "محمول": p,
                                "رسوم شهرية": g(0), "رسوم الخدمات": g(1),
                                "مكالمات محلية": g(2), "رسائل محلية": g(3), "إنترنت محلية": g(4),
                                "مكالمات دولية": g(5), "رسائل دولية": g(6), "مكالمات تجوال": g(7),
                                "رسائل تجوال": g(8), "إنترنت تجوال": g(9), "رسوم تسويات": g(10),
                                "ضرائب": g(11), "إجمالي": g(12)
                            })
    except Exception as e:
        print(f"Error: {e}")
    return records

# ================= UI =================
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"
st.image(logo_url, width=300)

files = st.file_uploader("📂 ارفعي ملفات PDF (عربي أو إنجليزي)", type=["pdf"], accept_multiple_files=True)
mode = st.radio("وضع اللغة", ["Auto 🤖", "عربي 🇪🇬", "English 🇺🇸"], horizontal=True)

if st.button("🚀 تحليل البيانات"):
    if files:
        prog = st.progress(0)
        all_data = []
        for idx, file in enumerate(files):
            # تحديد اللغة لكل ملف بشكل منفصل تماماً
            f_lang = None
            if mode == "عربي 🇪🇬": f_lang = "ar"
            elif mode == "English 🇺🇸": f_lang = "en"
            
            data = parse_file(file, force_lang=f_lang)
            all_data.extend(data)
            prog.progress((idx + 1) / len(files))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)
            st.markdown("### 📈 النتائج")
            cols = st.columns(5)
            cols[0].metric("الخطوط", len(df))
            cols[1].metric("الرسوم", f"{df['رسوم شهرية'].sum():,.1f}")
            cols[2].metric("التسويات", f"{df['رسوم تسويات'].sum():,.1f}")
            cols[3].metric("الضرائب", f"{df['ضرائب'].sum():,.1f}")
            cols[4].metric("الإجمالي", f"{df['إجمالي'].sum():,.1f}")
            
            st.dataframe(df, use_container_width=True)
            
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df.to_excel(w, index=False)
            st.download_button("📥 تحميل Excel", data=buf.getvalue(), file_name="Telecom_Report.xlsx")
        else:
            st.error("مفيش بيانات طلعت! اتأكدي من شكل الملف.")
