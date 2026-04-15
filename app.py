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
# ✅ UI ONLY
# =========================================================

def build_ui():
    st.markdown("""
    <style>
    body {
        font-family: 'Cairo', sans-serif !important;
        background-color: #f0fdf4;
    }

    .header {
        background: linear-gradient(135deg, #059669, #10b981);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin-bottom: 30px;
    }

    .header img {
        width: 220px;
    }

    .upload-box {
        background: white;
        border: 2px dashed #10b981;
        border-radius: 16px;
        padding: 50px;
        text-align: center;
        margin-bottom: 20px;
    }

    .stButton>button {
        font-size: 18px;
        padding: 16px;
        background: linear-gradient(90deg, #059669, #10b981);
        color: white;
        border-radius: 10px;
        width: 100%;
    }

    .kpi {
        background: white;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        border-top: 4px solid #10b981;
    }

    .success {
        background:#ecfdf5;
        border:2px solid #10b981;
        padding:20px;
        border-radius:12px;
        text-align:center;
        margin-top:20px;
    }
    </style>
    """, unsafe_allow_html=True)

    if logo:
        st.markdown(f"""
        <div class="header">
            <img src="data:image/png;base64,{logo}">
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="upload-box"></div>', unsafe_allow_html=True)

    file = st.file_uploader("", type=["pdf"], label_visibility="collapsed")

    return file

def show_dashboard(df):
    total_lines = len(df)
    total_monthly = df["رسوم شهرية"].sum()
    total_settlement = df["رسوم تسويات"].sum()
    total_total = df["إجمالي"].sum()

    st.markdown("## 📊 Dashboard")

    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(f'<div class="kpi"><h3>{total_lines}</h3><p>عدد الخطوط</p></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi"><h3>{total_monthly:.2f}</h3><p>الرسوم الشهرية</p></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi"><h3>{total_settlement:.2f}</h3><p>التسويات</p></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi"><h3>{total_total:.2f}</h3><p>الإجمالي</p></div>', unsafe_allow_html=True)

# ================= MAIN =================
file = build_ui()

if file:

    st.info(f"📄 {file.name}")

    if st.button("🚀 بدء المعالجة"):

        progress = st.progress(0)

        with st.spinner("جاري المعالجة..."):

            progress.progress(40)

            data = parse_ar(file)

            progress.progress(80)

            if data:
                df = pd.DataFrame(data)

                progress.progress(100)

                show_dashboard(df)

                st.dataframe(df.head(10), use_container_width=True)

                excel = to_excel(df)

                st.markdown("""
                <div class="success">
                    ✅ تم التحويل بنجاح
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    "⬇️ تحميل Excel",
                    excel,
                    file_name="hawelha_invoice_data.xlsx"
                )

            else:
                st.error("No data found")

# ================= FOOTER =================
st.markdown("""
<div style="
margin-top:60px;
padding:30px;
text-align:center;
background:white;
border-radius:16px;
box-shadow:0 4px 20px rgba(0,0,0,0.05);
">

<p style="
font-size:26px;
font-weight:800;
background: linear-gradient(90deg, #059669, #10b981);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
margin:0;
">
Developed by Najat El Bakry
</p>

<p style="
font-size:14px;
color:#6b7280;
margin-top:8px;
">
© 2026 Hawelha Telecom. All Rights Reserved
</p>

</div>
""", unsafe_allow_html=True)
