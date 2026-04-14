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

# ========== دوال المعالجة ==========

# ترتيب الأعمدة النهائي المطلوب في الإكسل (نفس ترتيب الملف المرفق من اليمين لليسار بصرياً)
# في الباندا نرتبها من اليسار لليمين
FINAL_COLUMNS_ORDER = [
    'محمول', 
    'إجمالي', 
    'قيمة الضرائب', 
    'رسوم وتسويات اخري', 
    'إنترنت تجوال', 
    'رسائل تجوال', 
    'مكالمات تجوال', 
    'رسائل دولية', 
    'مكالمات دولية', 
    'إنترنت محلية', 
    'رسائل محلية', 
    'مكالمات محلية', 
    'رسوم الخدمات', 
    'رسوم شهرية'
]

def extract_numbers_from_text(text):
    """
    استخراج جميع الأرقام (الموجبة والسالبة والعشرية) من نص معين
    يحافظ على ترتيب الأرقام كما تظهر في النص (من اليسار لليمين)
    """
    if not text:
        return []
    
    # Pattern لاستخراج الأرقام مع الإشارة السالبة والكسور العشرية
    # يدعم: 45.5, -99.58, 780, 0, -49, إلخ
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, str(text))
    
    numbers = []
    for match in matches:
        try:
            num = float(match)
            numbers.append(num)
        except (ValueError, TypeError):
            continue
    
    return numbers

def extract_etisalat_data(uploaded_file):
    """استخراج البيانات من ملف PDF"""
    all_records = []
    
    with pdfplumber.open(uploaded_file) as pdf:
        # البدء من صفحة 3 (الفهارس تبدأ من 0)
        start_page = 2
        if len(pdf.pages) <= start_page:
            start_page = 0
            
        for page_num in range(start_page, len(pdf.pages)):
            page = pdf.pages[page_num]
            tables = page.extract_tables()
            
            if not tables:
                continue
                
            for table in tables:
                if not table or len(table) < 2:
                    continue
                    
                i = 0
                while i < len(table):
                    row = table[i]
                    if not row:
                        i += 1
                        continue
                    
                    # دمج محتويات الصف للبحث عن رقم الهاتف
                    row_text = ' '.join([str(cell).strip() for cell in row if cell])
                    
                    # البحث عن رقم محمول مصري (010, 011, 012, 015)
                    phone_match = re.search(r'(01[0125]\d{8})', row_text)
                    
                    if phone_match:
                        phone_number = phone_match.group(1)
                        
                        # البحث عن صف القيم (عادة يكون الصف التالي)
                        values = []
                        
                        # محاولة استخراج القيم من الصف الحالي أولاً
                        current_values = extract_numbers_from_text(row_text)
                        
                        # ثم من الصف التالي إذا وجد
                        if i + 1 < len(table):
                            next_row = table[i + 1]
                            next_row_text = ' '.join([str(c).strip() for c in next_row if c])
                            next_values = extract_numbers_from_text(next_row_text)
                            
                            # نختار الصف الذي يحتوي على عدد أكبر من القيم (عادة 13 قيمة)
                            if len(next_values) >= 10:
                                values = next_values
                                i += 1  # تخطي الصف التالي لأنه تم استخدامه
                            elif len(current_values) >= 10:
                                values = current_values
                        else:
                            if len(current_values) >= 10:
                                values = current_values
                        
                        # إنشاء سجل إذا وجدنا قيم
                        if values:
                            record = create_record(phone_number, values)
                            all_records.append(record)
                    
                    i += 1
    
    return all_records

def create_record(phone, values):
    """
    توزيع القيم المستخرجة على الأعمدة المطلوبة
    
    ملاحظة هامة:
    - القيم في الـ PDF تأتي مرتبة بصرياً من اليمين لليسار (عربي)
    - لكن عند استخراجها بـ pdfplumber تكون من اليسار لليمين
    - لذلك نقوم بعكس القائمة لمطابقة ترتيب أعمدة الإكسل
    
    ترتيب القيم في الـ PDF (بعد الاستخراج وعكسها):
    0: إجمالي
    1: قيمة الضرائب
    2: رسوم وتسويات اخري
    3: إنترنت تجوال
    4: رسائل تجوال
    5: مكالمات تجوال
    6: رسائل دولية
    7: مكالمات دولية
    8: إنترنت محلية
    9: رسائل محلية
    10: مكالمات محلية
    11: رسوم الخدمات
    12: رسوم شهرية
    """
    
    # عكس القيم لمطابقة الترتيب العربي (من اليمين لليسار)
    reversed_values = values[::-1] if values else []
    
    # دالة مساعدة لجلب القيمة بأمان مع التعامل مع القيم الفارغة
    def get_value(index, default=0.0):
        if index < len(reversed_values):
            val = reversed_values[index]
            return val if val is not None else default
        return default
    
    record = {
        'محمول': phone,
        'إجمالي': get_value(0),
        'قيمة الضرائب': get_value(1),
        'رسوم وتسويات اخري': get_value(2),
        'إنترنت تجوال': get_value(3),
        'رسائل تجوال': get_value(4),
        'مكالمات تجوال': get_value(5),
        'رسائل دولية': get_value(6),
        'مكالمات دولية': get_value(7),
        'إنترنت محلية': get_value(8),
        'رسائل محلية': get_value(9),
        'مكالمات محلية': get_value(10),
        'رسوم الخدمات': get_value(11),
        'رسوم شهرية': get_value(12),
    }
    
    return record

def convert_df_to_excel(df):
    """تحويل البيانات إلى ملف Excel قابل للتنزيل"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # التأكد من ترتيب الأعمدة كما في النموذج المطلوب
        existing_cols = [col for col in FINAL_COLUMNS_ORDER if col in df.columns]
        df.to_excel(writer, index=False, sheet_name='البيانات', columns=existing_cols)
    
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
                
                if records:
                    progress_bar.progress(50)
                    
                    df = pd.DataFrame(records)
                    
                    # ترتيب الأعمدة حسب النموذج المطلوب
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
                        positive_count = sum(1 for r in records for v in r.values() if isinstance(v, (int, float)) and v > 0)
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>{positive_count}</h3>
                            <p>قيم موجبة</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        negative_count = sum(1 for r in records for v in r.values() if isinstance(v, (int, float)) and v < 0)
                        st.markdown(f"""
                        <div class="stats-card">
                            <h3>{negative_count}</h3>
                            <p>تعويضات (سالب)</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ تم التحويل بنجاح!")
                    st.markdown("### 📋 معاينة البيانات (أول 10 سجلات):")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    excel_data = convert_df_to_excel(df)
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
