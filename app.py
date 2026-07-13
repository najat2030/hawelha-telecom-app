import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import re
import io
import gc

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide", page_icon="")

# ================= STYLE & THEME =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
.stApp { background-color: #f8f9fa; font-family: 'Tajawal', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.login-card { background: white; padding: 35px; border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); max-width: 430px; margin: 70px auto; text-align: center; }
.login-title { color: #1a7e43; font-size: 26px; font-weight: 800; margin-bottom: 20px; }
.royal-green-box, div.stButton > button { background-color: #1a7e43 !important; color: white !important; border-radius: 50px !important; border: 2px solid #146435 !important; font-weight: 600 !important; }
.header-container { background: white; padding: 10px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; text-align: center; }
.metric-card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-right: 5px solid #1a7e43; text-align: center; }
.metric-value { font-size: 32px !important; color: #1a7e43; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)

# ================= USERS DATA =================
def load_users():
    return {
        "noga": "19852026",
        "amany": "123456",
        "ayat": "987654",
        "ghada": "456789",
        "omniya": "654321",
        "hussein": "1119885757"
    }
users = load_users()

# ================= SESSION STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-card"><div class="login-title">🔐 تسجيل الدخول</div></div>', unsafe_allow_html=True)
        u = st.text_input("Username", placeholder="اسم المستخدم", label_visibility="collapsed")
        p = st.text_input("Password", placeholder="كلمة المرور", type="password", label_visibility="collapsed")
        if st.button("دخول"):
            if u.strip() in users and users[u.strip()] == p.strip():
                st.session_state.logged_in = True
                st.session_state.username = u.strip()
                st.rerun()
            else:
                st.error("خطأ في البيانات")
    st.stop()

# ================= HEADER =================
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"
col_out, col_logo, col_me = st.columns([1, 4, 1], vertical_alignment="center")
with col_out:
    if st.button(" خروج"):
        st.session_state.logged_in = False
        st.rerun()
with col_logo:
    st.markdown(f'<div class="header-container"><img src="{logo_url}" style="max-width: 650px; height: auto;"></div>', unsafe_allow_html=True)
with col_me:
    initial = st.session_state.username[0].upper()
    st.markdown(f'<div class="royal-green-box"><span>{initial}</span> مرحباً، {st.session_state.username}</div>', unsafe_allow_html=True)

# ================= LOGIC =================
def normalize(t):
    return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")

def parse_file_smart(file):
    records = []
    try:
        file_bytes = file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        # نبدأ من الصفحة الثالثة زي ما اتفقنا
        for page_num in range(2, len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # البحث عن كل أرقام الموبايل في الصفحة
            phones = re.findall(r'(01[0125]\d{8})', text)
            
            for phone in phones:
                # نجد موقع الرقم في النص
                idx = text.find(phone)
                if idx == -1: continue
                
                # ناخذ جزء كبير من النص بعد الرقم لاستخراج القيم
                # في فواتيركم، الأرقام بتيجي في سطر منفصل أو بعد الاسم مباشرة
                # هنبحث عن أقرب 13 رقم عشري بعد موقع الهاتف
                chunk = text[idx:idx+1000] 
                
                # استخراج كل الأرقام العشرية من هذا الجزء
                numbers = re.findall(r'-?\d+(?:\.\d+)?', chunk)
                
                # تحويلها لـ float واستبعاد رقم الهاتف نفسه
                vals = []
                for n in numbers:
                    try:
                        f_val = float(n)
                        if str(int(f_val)) != phone: # تأكد إن الرقم مش هو رقم التليفون
                            vals.append(f_val)
                    except:
                        pass
                
                # لو لقينا 13 رقم أو أكتر، نحاول نبني السجل
                if len(vals) >= 13:
                    # في الغالب الترتيب بيكون: شهري، خدمات، محلي مكالمات، محلي رسائل، محلي نت، دولي مكالمات... إلخ
                    # لكن أحياناً بيكون فيه أرقام زائدة قبلهم، فبنستخدم نفس منطق الـ Scoring بتاعك
                    
                    def build_record(v):
                        return {
                            "محمول": phone,
                            "رسوم شهرية": v[0] if len(v)>0 else 0,
                            "رسوم الخدمات": v[1] if len(v)>1 else 0,
                            "مكالمات محلية": v[2] if len(v)>2 else 0,
                            "رسائل محلية": v[3] if len(v)>3 else 0,
                            "إنترنت محلية": v[4] if len(v)>4 else 0,
                            "مكالمات دولية": v[5] if len(v)>5 else 0,
                            "رسائل دولية": v[6] if len(v)>6 else 0,
                            "مكالمات تجوال": v[7] if len(v)>7 else 0,
                            "رسائل تجوال": v[8] if len(v)>8 else 0,
                            "إنترنت تجوال": v[9] if len(v)>9 else 0,
                            "رسوم تسويات": v[10] if len(v)>10 else 0,
                            "ضرائب": v[11] if len(v)>11 else 0,
                            "إجمالي": v[12] if len(v)>12 else 0
                        }

                    def score_record(rec):
                        total_calc = sum([rec[k] for k in rec if k not in ["محمول", "إجمالي"]])
                        diff = abs(rec["إجمالي"] - total_calc)
                        score = 0
                        if diff <= 0.05: score += 1000
                        elif diff <= 0.10: score += 500
                        elif diff <= 0.50: score += 250
                        elif diff <= 1: score += 100
                        elif diff <= 3: score += 30
                        elif diff <= 10: score += 10
                        if rec["رسوم شهرية"] >= 0: score += 10
                        if rec["ضرائب"] >= 0: score += 10
                        return score

                    # نجرب أول 13 رقم، ونجرب شيفت واحد، ونختار الأعلى سكور
                    candidates = []
                    for start in range(min(5, len(vals)-13)): # نجرب أول 5 احتمالات للبدء
                        window = vals[start:start+13]
                        rec = build_record(window)
                        candidates.append((score_record(rec), rec))
                    
                    if candidates:
                        best_rec = max(candidates, key=lambda x: x[0])[1]
                        # نتأكد إن الإجمالي مش صفر عشان نتجنب الأخطاء
                        if best_rec["إجمالي"] > 0:
                            records.append(best_rec)

        doc.close()
    except Exception as e:
        st.error(f"خطأ في المعالجة: {str(e)}")
    return records

# ================= UI =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

if st.button("🚀 بدء المعالجة والتحليل"):
    if files:
        progress_bar = st.progress(0)
        all_data = []
        for idx, file in enumerate(files):
            file.seek(0)
            data = parse_file_smart(file)
            all_data.extend(data)
            progress_bar.progress((idx + 1) / len(files))
            gc.collect()

        if all_data:
            df = pd.DataFrame(all_data)
            
            st.markdown("### 📈 ملخص التحليل المالي")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-title">📱 الخطوط</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-title">💰 الرسوم</div><div class="metric-value">{df["رسوم شهرية"].sum():,.1f}</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-title">🧾 تسويات</div><div class="metric-value" style="color: red;">{df["رسوم تسويات"].sum():,.1f}</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-title">🏛️ ضرائب</div><div class="metric-value">{df["ضرائب"].sum():,.1f}</div></div>', unsafe_allow_html=True)
            with m5:
                st.markdown(f'<div class="metric-card"><div class="metric-title">💎 الإجمالي</div><div class="metric-value">{df["إجمالي"].sum():,.1f}</div></div>', unsafe_allow_html=True)

            st.dataframe(df.head(50), use_container_width=True)
            if len(df) > 50:
                st.caption(f"️ تم عرض أول 50 سجل فقط. إجمالي السجلات: {len(df)}")

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            st.download_button(" تحميل تقرير Excel", data=buf.getvalue(), file_name="Telecom_Report.xlsx")
            
            del df, all_data, buf
            gc.collect()
