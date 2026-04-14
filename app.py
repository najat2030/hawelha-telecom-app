import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import io
import base64
import os

# ========== إعدادات الصفحة ==========
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== تحميل الشعار ==========
def load_logo():
    """تحميل الشعار إذا كان موجوداً"""
    logo_path = 'static/logo.png'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_data = base64.b64encode(f.read()).decode()
            return logo_data
    return None

# ========== CSS مخصص ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white;
        padding: 2.5rem 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(5,150,105,0.3);
    }
    .main-header h1 { font-size: 2.5rem; margin: 0; font-weight: 700; }
    .main-header p { 
        font-size: 1.3rem; 
        margin: 1rem 0 0.5rem 0; 
        opacity: 0.95; 
    }
    .logo-container { 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        margin-bottom: 1.5rem;
    }
    .logo-img { 
        max-width: 95%; 
        max-height: 250px; 
        width: auto; 
        height: auto;
        border-radius: 15px; 
        background: white; 
        padding: 25px;
        object-fit: contain;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .upload-box {
        background: #f0fdf4;
        border: 3px dashed #10b981;
        border-radius: 15px;
        padding: 3rem 2rem;
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
        padding: 2rem;
        margin-top: 3rem;
        border-radius: 10px;
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
</style>
""", unsafe_allow_html=True)

# ========== الشريط الجانبي ==========
with st.sidebar:
    st.title("📋 قائمة التحويل")
    st.markdown("""
    ### 📊 الأعمدة المستخرجة (14):
    1. محمول
    2. رسوم شهرية
    3. رسوم الخدمات
    4. مكالمات محلية
    5. رسائل محلية
    6. إنترنت محلية
    7. مكالمات دولية
    8. رسائل دولية
    9. مكالمات تجوال
    10. رسائل تجوال
    11. إنترنت تجوال
    12. رسوم وتسويات أخرى
    13. قيمة الضرائب
    14. إجمالي
    """)
    st.markdown("---")
    st.info("💡 **ملاحظة:** يبدأ الاستخراج من صفحة 3")

# ========== الهيدر مع الشعار ==========
logo_data = load_logo()

# تصحيح الخطأ: تم إضافة : وتعديل اسم المتغير
if logo_data:
    st.markdown(f"""
    <div class="main-header">
        <div class="logo-container">
            <img class="logo-img" src="data:image/png;base64,{logo_data}" alt="Hawelha Logo">
        </div>
        <p style="font-size: 1.2rem; margin-top: 0.5rem;">احترافي • سريع • دقيق</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Hawelha Telecom | حوّلها تليكوم</h1>
        <p style="font-size: 1.1rem; margin-top: 0.5rem;">احترافي • سريع • دقيق</p>
    </div>
    """, unsafe_allow_html=True)

# ========== دوال المعالجة ==========
def detect_language(text):
    if not text: return 'english'
    arabic_pattern = r'[\u0600-\u06FF]'
    arabic_chars = len(re.findall(arabic_pattern, text))
    total_chars = len(text.replace(' ', ''))
    if total_chars == 0: return 'english'
    return 'arabic' if (arabic_chars / total_chars) > 0.3 else 'english'

def extract_etisalat_data(uploaded_file):
    all_records = []
    detected_lang = None
    with pdfplumber.open(uploaded_file) as pdf:
        for page_num in range(2, min(5, len(pdf.pages))):
            page_text = pdf.pages[page_num].extract_text() or ''
            if page_text.strip():
                detected_lang = detect_language(page_text)
                break
        if detected_lang is None: detected_lang = 'english'
        for page_num in range(2, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    page_records = parse_etisalat_table(table, detected_lang)
                    all_records.extend(page_records)
    return all_records, detected_lang

def extract_values_from_row(row, is_arabic=True):
    values = []
    if not row: return values
    cells_to_process = reversed(row) if is_arabic else row
    for cell in cells_to_process:
        if not cell: continue
        cell_text = str(cell).strip()
        numbers = re.findall(r'-?\d+\.?\d*', cell_text)
        for num in numbers:
            try:
                val = float(num)
                if val != 0 and abs(val) <= 1000000:
                    values.append(val)
            except: pass
    return values

def parse_etisalat_table(table, language='arabic'):
    records = []
    if not table or len(table) < 2: return records
    is_arabic = (language == 'arabic')
    i = 0
    while i < len(table):
        row = table[i]
        if not row:
            i += 1
            continue
        row_text = ' '.join([str(cell) if cell else '' for cell in row])
        phone_match = re.search(r'(01[0125]\d{8})', row_text)
        if phone_match:
            phone = phone_match.group(1)
            values = []
            if i + 1 < len(table):
                values_row = table[i + 1]
                values = extract_values_from_row(values_row, is_arabic)
            records.append(create_record(phone, values))
            i += 2
        else: i += 1
    return records

def create_record(phone, values):
    return {
        'محمول': phone,
        'رسوم شهرية': values[0] if len(values) > 0 else 0,
        'رسوم الخدمات': values[1] if len(values) > 1 else 0,
        'مكالمات محلية': values[2] if len(values) > 2 else 0,
        'رسائل محلية': values[3] if len(values) > 3 else 0,
        'إنترنت محلية': values[4] if len(values) > 4 else 0,
        'مكالمات دولية': values[5] if len(values) > 5 else 0,
        'رسائل دولية': values[6] if len(values) > 6 else 0,
        'مكالمات تجوال': values[7] if len(values) > 7 else 0,
        'رسائل تجوال': values[8] if len(values) > 8 else 0,
        'إنترنت تجوال': values[9] if len(values) > 9 else 0,
        'رسوم وتسويات اخري': values[10] if len(values) > 10 else 0,
        'قيمة الضرائب': values[11] if len(values) > 11 else 0,
        'إجمالي': values[12] if len(values) > 12 else (values[-1] if values else 0)
    }

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='البيانات')
    output.seek(0)
    return output

# ========== المنطقة الرئيسية ==========
st.markdown("""
<div class="upload-box">
    <h2>📁 ارفع ملف الفاتورة (PDF)</h2>
    <p>يدعم الملفات الكبيرة - يبدأ الاستخراج من صفحة 3</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

if uploaded_file is not None:
    st.success(f"✅ تم رفع الملف: **{uploaded_file.name}**")
    if st.button("🚀 بدء التحويل الآن"):
        with st.spinner('⏳ جاري معالجة الملف...'):
            try:
                records, lang = extract_etisalat_data(uploaded_file)
                if records:
                    df = pd.DataFrame(records)
                    cols = ['محمول', 'رسوم شهرية', 'رسوم الخدمات', 'مكالمات محلية', 'رسائل محلية', 'إنترنت محلية', 'مكالمات دولية', 'رسائل دولية', 'مكالمات تجوال', 'رسائل تجوال', 'إنترنت تجوال', 'رسوم وتسويات اخري', 'قيمة الضرائب', 'إجمالي']
                    df = df[cols]
                    
                    st.info(f"📄 نوع الفاتورة: {'عربي 🇸🇦' if lang == 'arabic' else 'إنجليزي 🇬🇧'}")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.markdown(f'<div class="stats-card"><h3>{len(records)}</h3><p>عدد السجلات</p></div>', unsafe_allow_html=True)
                    
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    excel_data = convert_df_to_excel(df)
                    st.download_button("📥 تنزيل ملف Excel", data=excel_data, file_name=f"Hawelha_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)
                else:
                    st.error("⚠️ لم يتم العثور على سجلات.")
            except Exception as e:
                st.error(f"❌ حدث خطأ: {str(e)}")

st.markdown("""<div class="footer"><p>تم التطوير بواسطة <span style="color: #10b981; font-weight: 700;">Najat El Bakry</span></p></div>""", unsafe_allow_html=True)
