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

# ================= UI =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Tajawal:wght@400;500;700&display=swap');

html, body {
    font-family: 'Tajawal', 'Cairo', sans-serif;
    background: #f8fafc;
}

/* HEADER */
.header {
    background: linear-gradient(135deg, #059669, #10b981);
    padding: 50px 20px;
    border-radius: 18px;
    text-align: center;
    color: white;
    margin-bottom: 30px;
}

.header img {
    width: 480px;
    max-width: 95%;
    margin-bottom: 20px;
}

/* UPLOAD */
.upload-box {
    background: white;
    border: 2px dashed #10b981;
    border-radius: 16px;
    padding: 45px;
    text-align: center;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
    font-weight: 700;
    padding: 12px;
    border-radius: 10px;
    width: 100%;
}

/* KPI */
.kpi {
    background: white;
    border-radius: 14px;
    padding: 18px;
    text-align: center;
    border-top: 4px solid #10b981;
}

.kpi h2 {
    color: #059669;
}

.kpi p {
    color: #64748b;
}

/* SUCCESS */
.success-box {
    background: linear-gradient(135deg, #ecfdf5, #d1fae5);
    border: 2px solid #10b981;
    border-radius: 20px;
    padding: 50px 20px;
    text-align: center;
    margin-top: 30px;
    animation: pop 0.6s ease;
    box-shadow: 0 10px 30px rgba(16,185,129,0.25);
}

.success-icon {
    font-size: 70px;
}

.success-box h1 {
    font-size: 42px;
    font-weight: 700;
    color: #065f46;
}

.success-box h2 {
    font-size: 28px;
    color: #047857;
}

.success-box p {
    font-size: 18px;
    color: #065f46;
}

/* FOOTER */
.footer {
    background: #ffffff;
    border-top: 2px solid #10b981;
    margin-top: 60px;
    padding: 30px;
    text-align: center;
    border-radius: 12px;
}

.footer h3 {
    color: #059669;
    margin: 0;
    font-size: 20px;
}

.footer p {
    color: #6b7280;
    margin-top: 5px;
    font-size: 14px;
}

@keyframes pop {
    0% { transform: scale(0.7); opacity: 0; }
    100% { transform: scale(1); opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
if logo:
    st.markdown(f"""
    <div class="header">
        <img src="data:image/png;base64,{logo}">
        <h1>Hawelha Telecom</h1>
        <p>PDF → Excel Automation System</p>
    </div>
    """, unsafe_allow_html=True)

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', text)]

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
                        vals = extract_numbers(
                            " ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else ""
                        )
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

# ================= INPUT =================
st.markdown("""
<div class="upload-box">
    <h2>📁 Upload PDF Invoice</h2>
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

                total_lines = len(df)
                total_monthly = df["رسوم شهرية"].sum()
                total_settlement = df["رسوم تسويات"].sum()
                total_total = df["إجمالي"].sum()

                st.markdown("## 📊 Dashboard")

                c1, c2, c3, c4 = st.columns(4)

                c1.markdown(f'<div class="kpi"><h2>{total_lines}</h2><p>عدد الخطوط</p></div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="kpi"><h2>{total_monthly:.2f}</h2><p>الرسوم الشهرية</p></div>', unsafe_allow_html=True)
                c3.markdown(f'<div class="kpi"><h2>{total_settlement:.2f}</h2><p>التسويات</p></div>', unsafe_allow_html=True)
                c4.markdown(f'<div class="kpi"><h2>{total_total:.2f}</h2><p>الإجمالي</p></div>', unsafe_allow_html=True)

                st.dataframe(df.head(10), use_container_width=True)

                excel = to_excel(df)

                st.markdown("""
                <div class="success-box">
                    <div class="success-icon">🎉</div>
                    <h1>تم تحويل الملف بنجاح</h1>
                    <h2>الملف جاهز الآن للتحميل</h2>
                    <p>يمكنك تحميل الملف ومراجعته فورًا</p>
                </div>
                """, unsafe_allow_html=True)

                st.download_button(
                    "📥 تحميل Excel",
                    excel,
                    file_name="hawelha_telecom.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            else:
                st.error("لم يتم العثور على بيانات")

# ================= FOOTER =================
st.markdown("""
<div class="footer">
    <h3>Hawelha Telecom — Built by Najat El Bakry</h3>
    <p>© 2026 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)
