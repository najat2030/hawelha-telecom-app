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
    ### 📊 الأعمدة المستخرجة:
    1. محمول
    2. رسوم شهريه
    3. رسوم الخدمات
    4. رسوم محلية وتشمل 3 أعمدة
    4.1 مكالمات
    4.2 رسائل 
    4.3 إنترنت
    5. رسوم دولية وتشمل عامودين
    5.1 مكالمات
    5.2 رسائل 
    6. رسوم تجوال وتشمل 3 أعمدة
    6.1 مكالمات 
    6.2 رسائل
    6.3 إنترنت
    7. رسوم وتسويات أخرى
    8. قيمة الضرائب
    9. إجمالي
    """)
    
    st.markdown("---")
    st.info("💡 **ملاحظة:** يتم مطابقة الأعمدة بدقة مع نموذج الإكسل المرجعي.")

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

# ========== دوال المعالجة ==========
# ترتيب الأعمدة النهائي المطلوب في الإكسل (نفس ترتيب الصورة المرفقة من اليسار لليمين)
# ملاحظة: في الباندا (DataFrame) نرتبها من اليسار لليمين
FINAL_COLUMNS_ORDER = [
    'محمول', 
    'رسوم شهريه', 
    'رسوم الخدمات', 
    'رسوم محلية', 
    'رسائل محلية', 
    'إنترنت محلية', 
    'مكالمات دولية', 
    'رسائل دولية', 
    'إنترنت دولية', 
    'مكالمات تجوال', 
    'رسائل تجوال', 
    'إنترنت تجوال', 
    'رسوم وتسويات اخري', 
    'قيمة الضرائب', 
    'إجمالي'
]

def extract_numbers_from_line(line_text):
    """
    استخراج جميع الأرقام (الموجبة والسالبة) من سطر النص.
    يعيد قائمة بالأرقام بنفس ترتيب ظهورها في النص (من اليسار لليمين).
    """
    if not line_text:
        return []
    
    # Regex يجد الأرقام الصحيحة والعشرية، ويأخذ في الاعتبار الإشارة السالبة
    # Pattern: optional minus, digits, optional dot, optional digits
    pattern = r'-?\d+\.\d+|-?\d+'
    matches = re.findall(pattern, str(line_text))
    
    numbers = []
    for match in matches:
        try:
            numbers.append(float(match))
        except ValueError:
            continue
    return numbers

def extract_etisalat_data(uploaded_file):
    """استخراج البيانات من ملف PDF"""
    all_records = []
    
    with pdfplumber.open(uploaded_file) as pdf:
        # معالجة الصفحات (عادة الفواتير تبدأ من صفحة معينة، هنا نبدأ من 0 ونبحث عن الأنماط)
        # بناءً على الكود السابق، كان يبدأ من صفحة 3 (index 2)
        start_page_index = 2 
        if len(pdf.pages) <= start_page_index:
            start_page_index = 0 # Fallback if file is small
            
        for page_num in range(start_page_index, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()
            
            if tables:
                for table in tables:
                    # نمر على الجدول صف بصف
                    i = 0
                    while i < len(table):
                        row = table[i]
                        if not row:
                            i += 1
                            continue
                            
                        # دمج محتويات الصف للبحث عن رقم الهاتف
                        row_content = ' '.join([str(cell) if cell else '' for cell in row])
                        
                        # البحث عن نمط رقم المحمول المصري
                        phone_match = re.search(r'(01[0125]\d{8})', row_content)
                        
                        if phone_match:
                            phone_number = phone_match.group(1)
                            
                            # القيم عادة تكون في الصف التالي (أو نفس الصف في خلايا مختلفة)
                            # بناءً على ملف الـ PDF المرفق، القيم في سطر منفصل تحت الاسم
                            # سنحاول البحث في الصف الحالي أولاً، ثم التالي
                            
                            values_line_text = ""
                            
                            # 1. بحث في الصف الحالي (إذا كانت القيم مبعثرة)
                            current_row_numbers = extract_numbers_from_line(row_content)
                            
                            # 2. بحث في الصف التالي (الأغلب هنا)
                            if i + 1 < len(table):
                                next_row = table[i+1]
                                next_row_content = ' '.join([str(c) if c else '' for c in next_row])
                                next_row_numbers = extract_numbers_from_line(next_row_content)
                                
                                # نختار الصف الذي يحتوي على عدد أكبر من الأرقام (عادة 14 رقم)
                                if len(next_row_numbers) >= 10: # threshold
                                    values_line_text = next_row_content
                                    i += 1 # Skip next row as we consumed it
                                elif len(current_row_numbers) >= 10:
                                    values_line_text = row_content
                            else:
                                if len(current_row_numbers) >= 10:
                                    values_line_text = row_content

                            # استخراج القيم النهائية
                            final_values = extract_numbers_from_line(values_line_text)
                            
                            if final_values:
                                record = create_record(phone_number, final_values)
                                all_records.append(record)
                        
                        i += 1
    
    return all_records

def create_record(phone, values):
    """
    توزيع القيم على الأعمدة.
    القيم في الـ PDF تأتي عادة مرتبة بصرياً من اليمين لليسار (شهرية -> إجمالي).
    وبما أن Regex يقرأ من اليسار لليمين، فالقائمة `values` ستكون:
    [شهرية, خدمات, محلي-مكالمات, ..., إجمالي]
    """
    
    # دالة مساعدة لجلب القيمة بأمان
    def get_val(index):
        if index < len(values):
            return values[index]
        return 0.0

    record = {
        'محمول': phone,
        'رسوم شهرية': get_val(0),
        'رسوم الخدمات': get_val(1),
        'مكالمات محلية': get_val(2),
        'رسائل محلية': get_val(3),
        'إنترنت محلية': get_val(4),
        'مكالمات دولية': get_val(5),
        'رسائل دولية': get_val(6),
        'إنترنت دولية': get_val(7),
        'مكالمات تجوال': get_val(8),
        'رسائل تجوال': get_val(9),
        'إنترنت تجوال': get_val(10),
        'رسوم وتسويات اخري': get_val(11),
        'قيمة الضرائب': get_val(12),
        'إجمالي': get_val(13) # نأخذ آخر قيمة كإجمالي لضمان الدقة
    }
    return record

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # نعيد ترتيب الأعمدة لتكون مطابقة تماماً للطلب
        # نتأكد من وجود الأعمدة قبل الترتيب
        existing_cols = [c for c in FINAL_COLUMNS_ORDER if c in df.columns]
        df.to_excel(writer, index=False, sheet_name='البيانات', columns=existing_cols)
    output.seek(0)
    return output

# ========== المنطقة الرئيسية ==========
st.markdown("""
<div class="upload-box">
    <h2>📁 ارفع ملف الفاتورة (PDF)</h2>
    <p>سيقوم النظام بمطابقة الأعمدة مع نموذج الإكسل المرجعي تلقائياً</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(" ", type=['pdf'], label_visibility="collapsed")

if uploaded_file is not None:
    st.success(f"✅ تم رفع الملف: **{uploaded_file.name}**")
    
    if st.button("🚀 بدء التحويل الآن"):
        with st.spinner('⏳ جاري معالجة الملف ومطابقة الأعمدة...'):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔍 جاري استخراج البيانات من PDF...")
                records = extract_etisalat_data(uploaded_file)
                
                if records:
                    progress_bar.progress(50)
                    
                    df = pd.DataFrame(records)
                    
                    # ترتيب الأعمدة
                    # نتأكد من ترتيب الأعمدة حسب القائمة النهائية
                    df = df.reindex(columns=FINAL_COLUMNS_ORDER)
                    
                    progress_bar.progress(80)
                    
                    st.markdown("### 📊 إحصائيات التحويل:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>{len(records)}</h3>
                            <p>عدد السجلات</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        # حساب مجموع العمود الإجمالي كمثال
                        total_sum = df['إجمالي'].sum() if 'إجمالي' in df.columns else 0
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>{total_sum:,.2f}</h3>
                            <p>إجمالي الفاتورة</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>15</h3>
                            <p>عدد الأعمدة</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ تم التحويل بنجاح!")
                    
                    st.markdown("### 📋 معاينة البيانات (أول 10 سجلات):")
                    # تنسيق الأرقام في العرض
                    st.dataframe(df.head(10).style.format("{:,.2f}", subset=df.select_dtypes(include=['float', 'int']).columns), use_container_width=True)
                    
                    excel_data = convert_df_to_excel(df)
                    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                    file_name = f'Hawelha_Telecom_{date_str}.xlsx'
                    
                    st.markdown("""
                    <div class="success-box">
                        <h3>🎉 تم التحويل بنجاح!</h3>
                        <p>الملف جاهز للتنزيل بنفس هيكلية الإكسل المطلوبة</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.download_button(
                        label="📥 تنزيل ملف Excel",
                        data=excel_data,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.error("⚠️ لم يتم العثور على أي سجلات. تأكد أن الملف يحتوي على جداول من صفحة 3")
            except Exception as e:
                st.error(f"❌ حدث خطأ: {str(e)}")

# ========== الفوتر ==========
st.markdown("""
<div class="footer">
    <p style="margin: 0; font-size: 1.1rem;">
        تم التطوير بواسطة 
        <span style="color: #10b981; font-weight: 700;">Najat El Bakry</span>
    </p>
    <p style="margin: 0.5rem 0 0 0; opacity: 0.8; font-size: 0.9rem;">
        Hawelha Telecom © 2026 - جميع الحقوق محفوظة
    </p>
</div>
""", unsafe_allow_html=True)
