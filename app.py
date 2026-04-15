import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os

# ================= CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= LOGO =================
def load_logo():
    path = "static/logo.png"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo = load_logo()

# =========================================================
# ❌❌ DO NOT MODIFY BELOW THIS LINE (CORE LOGIC) ❌❌❌
# =========================================================

def normalize(text):
    return (text or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    matches = re.findall(r'(-?\s*\d+(?:\.\d+)?\s*-?)', text)

    numbers = []
    for m in matches:
        m = m.replace(" ", "")
        if m.endswith("-"):
            val = -float(m[:-1])
        else:
            val = float(m)
        numbers.append(val)

    return numbers

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

                        vals = vals[::-1]

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

def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# =========================================================
# ✅✅✅ UI SECTION ONLY (SAFE TO MODIFY) ✅✅✅
# =========================================================

def build_ui():
    # Import Google Font Cairo for better Arabic typography
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        /* Global Styles */
        body {
            font-family: 'Cairo', sans-serif !important;
            background-color: #f0fdf4; /* Light green tint */
        }
        
        /* Header Styling */
        .main-header {
            background: linear-gradient(135deg, #047857 0%, #10b981 100%);
            padding: 3rem 2rem;
            border-radius: 20px;
            text-align: center;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .logo-img {
            max-width: 350px; /* Larger Logo */
            height: auto;
            margin-bottom: 1rem;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
        }

        .app-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: 1px;
        }

        .app-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }

        /* Upload Box Styling */
        .upload-container {
            background: white;
            border: 2px dashed #10b981;
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
            transition: all 0.3s ease;
            margin-bottom: 2rem;
        }
        .upload-container:hover {
            border-color: #047857;
            background: #ecfdf5;
        }

        /* KPI Cards Styling */
        .kpi-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-top: 5px solid #10b981;
            height: 100%;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #047857;
            margin: 0.5rem 0;
        }
        .kpi-label {
            color: #6b7280;
            font-size: 0.9rem;
            font-weight: 600;
        }

        /* Footer Styling */
        .footer {
            margin-top: 4rem;
            padding: 2rem;
            text-align: center;
            color: #047857;
            border-top: 1px solid #d1fae5;
        }
        .developer-name {
            font-weight: 700;
            font-size: 1.1rem;
            color: #047857;
        }
        .copyright {
            font-size: 0.85rem;
            color: #6b7280;
            margin-top: 0.5rem;
        }
        
        /* Button Styling */
        .stButton>button {
            background: linear-gradient(90deg, #047857 0%, #10b981 100%);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 8px;
            width: 100%;
            transition: transform 0.2s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }
    </style>
    """, unsafe_allow_html=True)

    # Header Section with Large Logo
    if logo:
        st.markdown(f"""
        <div class="main-header">
            <img class="logo-img" src="data:image/png;base64,{logo}" alt="Hawelha Logo">
            <h1 class="app-title">Hawelha Telecom</h1>
            <p class="app-subtitle">نظام تحويل فواتير الاتصالات الذكي من PDF إلى Excel</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="main-header">
            <h1 class="app-title">Hawelha Telecom</h1>
            <p class="app-subtitle">نظام تحويل فواتير الاتصالات الذكي</p>
        </div>
        """, unsafe_allow_html=True)

    # Upload Section
    st.markdown('<div class="upload-container"><h2>📁 رفع ملف الفاتورة (PDF)</h2><p style="color:#6b7280">اسحب الملف هنا أو اضغط للاختيار</p></div>', unsafe_allow_html=True)
    file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")

    return file

def show_dashboard(df):
    total_lines = len(df)
    total_monthly = df["رسوم شهرية"].sum()
    total_settlement = df["رسوم تسويات"].sum()
    total_total = df["إجمالي"].sum()

    st.markdown("## 📊 لوحة المعلومات")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">عدد الخطوط</div><div class="kpi-value">{total_lines}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">الرسوم الشهرية</div><div class="kpi-value">{total_monthly:,.2f} ج.م</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">التسويات</div><div class="kpi-value">{total_settlement:,.2f} ج.م</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">الإجمالي النهائي</div><div class="kpi-value">{total_total:,.2f} ج.م</div></div>', unsafe_allow_html=True)

    st.markdown("---")

# ================= MAIN =================
file = build_ui()

if file:
    if st.button("🚀 بدء المعالجة"):
        with st.spinner("جاري معالجة البيانات... يرجى الانتظار"):

            data = parse_ar(file)

            if data:
                df = pd.DataFrame(data)

                show_dashboard(df)

                st.markdown("### 📋 معاينة البيانات (أول 10 سجلات)")
                st.dataframe(df.head(10), use_container_width=True)

                excel = to_excel(df)

                st.download_button(
                    "📥 تحميل ملف Excel",
                    excel,
                    file_name="Hawelha_Invoice_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Footer with Name and Copyright
                st.markdown("""
                <div class="footer">
                    <p class="developer-name">Developed by Najat El Bakry</p>
                    <p class="copyright">© 2026 Hawelha Telecom. All Rights Reserved.</p>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.error("⚠️ لم يتم العثور على بيانات في الملف. تأكد من صحة ملف PDF.")
