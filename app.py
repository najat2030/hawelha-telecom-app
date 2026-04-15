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
# ❌❌❌ DO NOT MODIFY BELOW THIS LINE (CORE LOGIC) ❌❌❌
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
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
        
        body {
            font-family: 'Cairo', sans-serif !important;
            background-color: #f0fdf4;
        }
        
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
        }
        .kpi-label {
            color: #6b7280;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .footer {
            margin-top: 4rem;
            padding: 2.5rem;
            text-align: center;
        }

        .developer-name {
            font-size: 2.2rem;
            font-weight: 800;
            color: #059669;
        }

        .copyright {
            font-size: 0.9rem;
            color: #9ca3af;
        }

        .stButton>button {
            background: linear-gradient(90deg, #059669 0%, #10b981 100%);
            color: white;
            border-radius: 10px;
            padding: 12px;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)

    # 🔥 اللوجو الكبير في النص
    if logo:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #059669, #10b981);
            padding: 70px 20px;
            border-radius: 25px;
            text-align: center;
            margin-bottom: 30px;
        ">
            <img src="data:image/png;base64,{logo}" style="
                width: 420px;
                max-width: 95%;
                display: block;
                margin: auto;
                filter: drop-shadow(0px 10px 25px rgba(0,0,0,0.25));
            ">
        </div>
        """, unsafe_allow_html=True)

    file = st.file_uploader("", type=["pdf"])

    return file

def show_dashboard(df):
    total_lines = len(df)
    total_monthly = df["رسوم شهرية"].sum()
    total_settlement = df["رسوم تسويات"].sum()
    total_total = df["إجمالي"].sum()

    st.markdown("### 📊 لوحة المعلومات")

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">عدد الخطوط</div><div class="kpi-value">{total_lines}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-label">الرسوم الشهرية</div><div class="kpi-value">{total_monthly:,.2f}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-label">التسويات</div><div class="kpi-value">{total_settlement:,.2f}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-label">الإجمالي</div><div class="kpi-value">{total_total:,.2f}</div></div>', unsafe_allow_html=True)

# ================= MAIN =================
file = build_ui()

if file:
    if st.button("🚀 بدء المعالجة"):
        with st.spinner("جاري المعالجة..."):

            data = parse_ar(file)

            if data:
                df = pd.DataFrame(data)

                show_dashboard(df)

                st.dataframe(df.head(10), use_container_width=True)

                excel = to_excel(df)

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name="hawelha_invoice_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.markdown("""
                <div class="footer">
                    <p class="developer-name">Developed by Najat El Bakry</p>
                    <p class="copyright">© 2026 Hawelha Telecom. All Rights Reserved</p>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.error("⚠️ لم يتم العثور على بيانات")
