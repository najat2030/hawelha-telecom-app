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
        * { font-family: 'Cairo', sans-serif !important; }
        
        .main-header {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            color: white;
            padding: 2rem 1rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(5,150,105,0.3);
        }
        
        .logo-container { 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            margin-bottom: 1rem;
        }
        
        .logo-img { 
            max-width: 200px; /* أصغر قليلاً للموبايل واللابتوب */
            height: auto;
            border-radius: 10px; 
            background: white; 
            padding: 20px;
            object-fit: contain;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        .upload-box {
            background: #f0fdf4;
            border: 3px dashed #10b981;
            border-radius: 15px;
            padding: 2.5rem 2rem;
            text-align: center;
        }

        .stats-card {
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-right: 4px solid #059669;
        }
        .stats-card h3 { color: #059669; margin: 0 0 0.5rem 0; font-size: 2rem; }
        .stats-card p { color: #6b7280; margin: 0; font-size: 0.9rem; }

        .footer {
            background: #1e293b;
            color: white;
            text-align: center;
            padding: 2.5rem 2rem;
            margin-top: 3rem;
            border-radius: 10px;
        }

        .developer-name {
            font-size: 2.2rem; /* مكبر جداً كما طلبت */
            font-weight: 700;
            color: #10b981;
            margin: 0;
            letter-spacing: 1px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .copyright {
            font-size: 1rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }

        .success-box {
            background: #dcfce7;
            border: 2px solid #16a34a;
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            margin: 1rem 0;
        }

        .stButton>button {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 8px;
            width: 100%;
        }

        .dataframe {
            direction: rtl !important;
            text-align: right !important;
        }
        .dataframe th, .dataframe td {
            text-align: right !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header without "Hawelha Telecom" title — only logo if exists
    if logo:
        st.markdown(f"""
        <div class="main-header">
            <div class="logo-container">
                <img class="logo-img" src="image/png;base64,{logo}" alt="Logo">
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # If no logo, show minimal header or nothing — as per your request to remove "Hawelha Telecom"
        st.markdown("""
        <div class="main-header" style="padding: 1rem;">
            <!-- Empty header since we removed the title -->
        </div>
        """, unsafe_allow_html=True)

    # Upload Box
    st.markdown("""
    <div class="upload-box">
        <h2>📁 ارفع ملف الفاتورة (PDF)</h2>
        <p>يدعم الملفات الكبيرة - يبدأ الاستخراج من صفحة 3</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

    return uploaded_file


def show_dashboard(df):
    total_lines = len(df)
    total_monthly = df["رسوم شهرية"].sum() if "رسوم شهرية" in df.columns else 0
    total_settlement = df["رسوم وتسويات اخري"].sum() if "رسوم وتسويات اخري" in df.columns else 0
    total_total = df["إجمالي"].sum() if "إجمالي" in df.columns else 0

    st.markdown("### 📊 إحصائيات التحويل:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{total_lines}</h3>
            <p>عدد السجلات</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{total_monthly:,.2f}</h3>
            <p>الرسوم الشهرية</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{total_total:,.2f}</h3>
            <p>الإجمالي</p>
        </div>
        """, unsafe_allow_html=True)


# ================= MAIN =================
file = build_ui()

if file:
    if st.button("🚀 بدء التحويل الآن"):
        with st.spinner('⏳ جاري معالجة الملف...'):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔍 جاري استخراج البيانات من PDF...")
                records = parse_ar(file)  # استخدمنا الدالة الصحيحة هنا
                
                if records:
                    progress_bar.progress(50)
                    
                    df = pd.DataFrame(records)
                    columns_order = [
                        'محمول', 'رسوم شهرية', 'رسوم الخدمات',
                        'مكالمات محلية', 'رسائل محلية', 'إنترنت محلية',
                        'مكالمات دولية', 'رسائل دولية',
                        'مكالمات تجوال', 'رسائل تجوال', 'إنترنت تجوال',
                        'رسوم وتسويات اخري', 'ضرائب', 'إجمالي'
                    ]
                    df = df[columns_order]
                    progress_bar.progress(80)
                    
                    show_dashboard(df)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ تم التحويل بنجاح!")
                    st.markdown("### 📋 معاينة البيانات (أول 10 سجلات):")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    excel_data = to_excel(df)
                    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_name = f'Hawelha_Telecom_{date_str}.xlsx'
                    
                    st.markdown("""
                    <div class="success-box">
                        <h3>🎉 تم التحويل بنجاح!</h3>
                        <p>اضغط على الزر أدناه لتنزيل الملف</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.download_button(
                        label="📥 تنزيل ملف Excel",
                        data=excel_data,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    # Footer with BIG and STYLISH developer name
                    st.markdown("""
                    <div class="footer">
                        <p class="developer-name">Developed by Najat El Bakry</p>
                        <p class="copyright">© 2026 جميع الحقوق محفوظة</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.error("⚠️ لم يتم العثور على أي سجلات. تأكد أن الملف يحتوي على جداول من صفحة 3")
            except Exception as e:
                st.error(f"❌ حدث خطأ: {str(e)}")
