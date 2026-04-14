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
    .dataframe th {
        text-align: right !important;
    }
    .dataframe td {
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

# ========== دوال المعالجة المُحسَّنة ==========
def extract_number(text):
    """استخراج رقم مع الحفاظ على الإشارة السالبة"""
    if not text:
        return 0.0
    
    text = str(text).strip()
    
    # البحث عن الأرقام مع الإشارة السالبة أو الموجبة
    patterns = [
        r'[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?',  # مع الفواصل والنقاط
        r'[-+]?\d+\.?\d*',                     # الأرقام العادية
        r'[-+]?\d+',                           # الأرقام الصحيحة
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                # إزالة الفواصل وتحويل إلى float
                clean_num = match.replace(',', '')
                num = float(clean_num)
                return num
            except ValueError:
                continue
    
    return 0.0

def extract_phone_number(row_text):
    """استخراج رقم المحمول بدقة أعلى"""
    phone_patterns = [
        r'01[0-2][0-9]{8}',  # أرقام مصرية صحيحة
        r'01[5][0-9]{8}',
        r'(01[0-2][0-9]{8})',
        r'(01[5][0-9]{8})',
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, row_text)
        if match:
            return match.group(1) if match.groups() else match.group(0)
    return None

def parse_etisalat_table(table):
    """معالجة جدول الفاتورة المُحسَّنة"""
    records = []
    
    if not table or len(table) < 2:
        return records
    
    # تحليل كل الصفوف للبحث عن أرقام الموبايل
    for i in range(len(table)):
        row = table[i]
        if not row:
            continue
            
        row_text = ' '.join(str(cell).strip() if cell else '' for cell in row)
        
        # البحث عن رقم المحمول
        phone = extract_phone_number(row_text)
        if not phone:
            continue
            
        # البحث عن صف الرسوم (الصف التالي أو صفوف مجاورة)
        values = []
        for j in range(max(0, i-2), min(len(table), i+3)):
            if j == i:
                continue
            value_row = table[j]
            row_values = [extract_number(cell) for cell in value_row if extract_number(cell) != 0]
            if row_values:
                values.extend(row_values)
                break
        
        # إذا لم نجد قيم كافية، نبحث في نفس الصف
        if len(values) < 3:
            row_values = [extract_number(cell) for cell in row if extract_number(cell) != 0]
            values.extend(row_values)
        
        # تكرار القيم إذا كانت قليلة
        while len(values) < 14:
            values.append(0.0)
        
        record = create_record(phone, values[:14])
        records.append(record)
        
        # تجنب تكرار نفس السجل
        i += 1
    
    return records

def create_record(phone, values):
    """إنشاء سجل مع توزيع صحيح للأعمدة"""
    column_mapping = [
        'رسوم شهرية',
        'رسوم الخدمات', 
        'مكالمات محلية',
        'رسائل محلية',
        'إنترنت محلية',
        'مكالمات دولية',
        'رسائل دولية',
        'مكالمات تجوال',
        'رسائل تجوال',
        'إنترنت تجوال',
        'رسوم وتسويات أخرى',
        'قيمة الضرائب',
        'إجمالي'
    ]
    
    record = {'محمول': phone}
    
    for i, column in enumerate(column_mapping):
        if i < len(values):
            record[column] = values[i]
        else:
            record[column] = 0.0
    
    return record

def extract_etisalat_data(uploaded_file):
    """استخراج البيانات من ملف PDF المُحسَّن"""
    all_records = []
    
    try:
        with pdfplumber.open(uploaded_file) as pdf:
            st.info(f"📄 تم العثور على {len(pdf.pages)} صفحة")
            
            # معالجة كل الصفحات من صفحة 3 فما فوق
            for page_num in range(2, len(pdf.pages)):
                page = pdf.pages[page_num]
                
                # استخراج النصوص الكاملة للصفحة للتحليل
                page_text = page.extract_text()
                if not page_text:
                    continue
                
                # استخراج الجداول
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables):
                        st.write(f"معالجة الجدول {table_num+1} في الصفحة {page_num+1}")
                        page_records = parse_etisalat_table(table)
                        all_records.extend(page_records)
                        
                        # عرض عينة من البيانات المستخرجة للتشخيص
                        if page_records:
                            st.write("عينة من السجلات المستخرجة:")
                            for record in page_records[:2]:
                                st.write(record)
                
                # إذا لم نجد جداول، نحاول استخراج النصوص
                else:
                    lines = page_text.split('\n')
                    for line in lines:
                        phone = extract_phone_number(line)
                        if phone:
                            st.write(f"رقم محمول في النص: {phone}")
    
    except Exception as e:
        st.error(f"خطأ في قراءة PDF: {str(e)}")
    
    return all_records

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # تنسيق العربية في Excel
        df.to_excel(writer, index=False, sheet_name='البيانات')
        
        # تحسين التنسيق
        worksheet = writer.sheets['البيانات']
        from openpyxl.styles import Font, Alignment
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # محاذاة النصوص لليمين
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(horizontal='right')
    
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
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔍 جاري استخراج البيانات من PDF...")
                records = extract_etisalat_data(uploaded_file)
                
                progress_bar.progress(50)
                
                if records:
                    df = pd.DataFrame(records)
                    
                    # ترتيب الأعمدة بشكل صحيح
                    columns_order = [
                        'محمول', 'رسوم شهرية', 'رسوم الخدمات',
                        'مكالمات محلية', 'رسائل محلية', 'إنترنت محلية',
                        'مكالمات دولية', 'رسائل دولية',
                        'مكالمات تجوال', 'رسائل تجوال', 'إنترنت تجوال',
                        'رسوم وتسويات أخرى', 'قيمة الضرائب', 'إجمالي'
                    ]
                    
                    # التأكد من وجود جميع الأعمدة
                    for col in columns_order:
                        if col not in df.columns:
                            df[col] = 0.0
                    
                    df = df[columns_order]
                    
                    progress_bar.progress(80)
                    
                    # إحصائيات محسنة
                    st.markdown("### 📊 إحصائيات التحويل:")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_records = len(df)
                    total_positive = (df.select_dtypes(include=['number']) > 0).sum().sum()
                    total_negative = (df.select_dtypes(include=['number']) < 0).sum().sum()
                    grand_total = df['إجمالي'].sum()
                    
                    with col1:
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>{total_records}</h3>
                            <p>عدد السجلات</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>{total_positive}</h3>
                            <p>قيم موجبة</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>{total_negative}</h3>
                            <p>تعويضات (سالب)</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>{grand_total:,.2f}</h3>
                            <p>إجمالي المبالغ</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ تم التحويل بنجاح!")
                    
                    st.markdown("### 📋 معاينة البيانات:")
                    st.dataframe(df, use_container_width=True)
                    
                    # تنزيل الملف
                    excel_data = convert_df_to_excel(df)
                    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_name = f'Hawelha_Telecom_{date_str}.xlsx'
                    
                    st.markdown("""
                    <div class="success-box">
                        <h3>🎉 تم التحويل بنجاح!</h3>
                        <p>اضغط على الزر أدناه لتنزيل ملف Excel</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.download_button(
                        label="📥 تنزيل ملف Excel",
                        data=excel_data.getvalue(),
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officerspreadsheetml.sheet"
                    )
                else:
                    st.error("""
                    ⚠️ **لم يتم العثور على بيانات.** 
                    تأكد من:
                    - الملف يحتوي على جداول في صفحة 3 فما فوق
                    - تنسيق الفاتورة مطابق لفواتير اتصالات
                    - أرقام الموبايل موجودة بالشكل 01xxxxxxxxx
                    """)
                    
            except Exception as e:
                st.error(f"❌ خطأ في المعالجة: {
