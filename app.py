import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import zipfile

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
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');

html, body {
    font-family: 'Cairo', sans-serif;
    background: #f8fafc;
}

.header {
    background: linear-gradient(135deg, #059669, #10b981);
    padding: 40px;
    border-radius: 18px;
    text-align: center;
    color: white;
}

.upload-box {
    background: white;
    border: 2px dashed #10b981;
    border-radius: 16px;
    padding: 45px;
    text-align: center;
}

.stButton>button {
    background: linear-gradient(135deg, #059669, #10b981);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ================= HEADER =================
if logo:
    st.markdown(f"""
    <div class="header">
        <img src="data:image/png;base64,{logo}" width="400">
        <h1>Hawelha Telecom</h1>
    </div>
    """, unsafe_allow_html=True)

# ================= HELPERS =================
def normalize(t):
    return (t or "").replace("−","-").replace("–","-")

def extract_numbers(text):
    text = normalize(text)
    text = re.sub(r'01[0125]\d{8}', '', text)
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', text)]

# ================= ENGINE =================
@st.cache_data(show_spinner=False)
def process_file(file_bytes, mode):

    records = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:

        if mode == "Auto 🤖":
            text = pdf.pages[0].extract_text() or ""
            lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
        else:
            lang = "ar" if mode == "عربي 🇪🇬" else "en"

        for page in pdf.pages[2:]:
            for table in page.extract_tables() or []:

                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue

                    text = normalize(" ".join([str(c) for c in row if c]))
                    phone_match = re.search(r'(01[0125]\d{8})', text)

                    if phone_match:
                        phone = phone_match.group(1)

                        values = extract_numbers(text)

                        if i+1 < len(table):
                            next_row = " ".join([str(c) for c in table[i+1] if c])
                            next_vals = extract_numbers(next_row)
                            if len(next_vals) > len(values):
                                values = next_vals
                                i += 1

                        values = values[::-1]

                        def g(i): return values[i] if i < len(values) else 0

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
    <h2>📁 Upload PDF Invoices</h2>
</div>
""", unsafe_allow_html=True)

files = st.file_uploader("", type=["pdf"], accept_multiple_files=True)

# ================= MAIN =================
if files:

    st.success(f"✅ تم رفع {len(files)} ملف")

    if st.button("🚀 Start Processing"):

        progress_bar = st.progress(0)
        status = st.empty()
        details = st.empty()

        total = len(files)
        all_excels = []

        for i, f in enumerate(files):

            current = i + 1
            percent = int((current / total) * 100)

            status.text(f"📄 جاري معالجة: {f.name}")
            details.text(f"📁 {current} من {total} ملفات | {percent}%")

            data = process_file(f.read(), mode)

            progress_bar.progress(percent)

            if data:
                df = pd.DataFrame(data)
                excel = to_excel(df)

                file_name = f.name.replace(".pdf", ".xlsx")
                all_excels.append((file_name, excel))

                st.markdown(f"### 📄 {f.name}")
                st.download_button(
                    f"📥 تحميل {file_name}",
                    excel,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning(f"⚠️ لم يتم استخراج بيانات من {f.name}")

        status.text("✅ تم الانتهاء من كل الملفات")

        # ================= ZIP =================
        if all_excels:
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, "w") as z:
                for name, file_data in all_excels:
                    z.writestr(name, file_data.getvalue())

            zip_buffer.seek(0)

            st.download_button(
                "📦 تحميل كل الملفات مرة واحدة (ZIP)",
                zip_buffer,
                file_name="hawelha_all_files.zip",
                mime="application/zip"
            )
