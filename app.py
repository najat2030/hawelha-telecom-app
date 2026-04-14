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
    logo_path = 'static/logo.png'
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

# ========== CSS مخصص ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white; padding: 2.5rem 2rem; border-radius: 15px;
        text-align: center; margin-bottom: 2rem; box-shadow: 0 4px 15px rgba(5,150,105,0.3);
    }
    .upload-box {
        background: #f0fdf4; border: 3px dashed #10b981;
        border-radius: 15px; padding: 2rem; text-align: center;
    }
    .stats-card {
        background: white; border-radius: 10px; padding: 1.5rem;
        text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-right: 4px solid #059669;
    }
</style>
""", unsafe_allow_html=True)

# ========== دوال المعالجة الذكية ==========

def detect_language(text):
    if not text: return 'english'
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars = len(text.replace(' ', ''))
    if total_chars == 0: return 'english'
    return 'arabic' if (arabic_chars / total_chars) > 0.2 else 'english'

def extract_numbers_from_row(row):
    """استخراج الأرقام فقط من صف الجدول وتجاهل النصوص"""
    nums = []
    for cell in row:
        if cell:
            # تنظيف الخلية من العملات أو النصوص والبقاء على الأرقام والسالب والنقطة
            clean_val = re.sub(r'[^\d\.\-]', '', str(cell))
            if clean_val and clean_val != '-':
                try:
                    nums.append(float(clean_val))
                except: continue
    return nums

def process_etisalat_pdf(uploaded_file):
    all_data = []
    final_lang = 'english'
    
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages[2:]:  # البدء من صفحة 3
            text = page.extract_text() or ""
            current_lang = detect_language(text)
            final_lang = current_lang # الاعتماد على لغة آخر صفحات البيانات
            
            tables = page.extract_tables()
            for table in tables:
                for i, row in enumerate(table):
                    row_str = " ".join([str(c) for c in row if c])
                    # البحث عن رقم الموبايل (يبدأ بـ 01)
                    phone_match = re.search(r'(01[0125]\d{8})', row_str)
                    
                    if phone_match:
                        phone = phone_match.group(1)
                        # محاولة جلب مبالغ السطر الحالي أو السطر التالي
                        values = extract_numbers_from_row(row)
                        # إذا كان رقم الهاتف هو الرقم الوحيد في السطر، نبحث في السطر التالي
                        if len(values) <= 1 and i+1 < len(table):
                            values = extract_numbers_from_row(table[i+1])
                        
                        # إزالة رقم الهاتف من قائمة المبالغ إذا وجد
                        values = [v for v in values if not str(int(v)).endswith(phone[1:])]
                        
                        # ترتيب المبالغ: لو عربي بنعكس المصفوفة لأن PDF بيقرأ الجداول بالعكس
                        if current_lang == 'arabic':
                            values = values[::-1]
                        
                        all_data.append(create_structured_record(phone, values))
    
    return all_data, final_lang

def create_structured_record(phone, v):
    """توزيع القيم على 14 عمود بدقة"""
    # نملأ المصفوفة بأصفار لو كانت ناقصة عشان الكود ميفصلش
    v = v + [0] * (13 - len(v)) 
    return {
        'محمول': phone,
        'رسوم شهرية': v[0], 'رسوم الخدمات': v[1], 'مكالمات محلية': v[2],
        'رسائل محلية': v[3], 'إنترنت محلية': v[4], 'مكالمات دولية': v[5],
        'رسائل دولية': v[6], 'مكالمات تجوال': v[7], 'رسائل تجوال': v[8],
        'إنترنت تجوال': v[9], 'رسوم وتسويات اخري': v[10], 'قيمة الضرائب': v[11],
        'إجمالي': v[12] if v[12] != 0 else sum(v[:12])
    }

def save_to_excel(df, lang):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='البيانات')
        # ضبط اتجاه الشيت (يمين ليسار للعربي)
        worksheet = writer.sheets['البيانات']
        if lang == 'arabic':
            worksheet.sheet_view.rightToLeft = True
    return output.getvalue()

# ========== الواجهة الأمامية ==========
logo_data = load_logo()
if logo_data:
    st.markdown(f'<div class="main-header"><img src="data:image/png;base64,{logo_data}" width="200"><p>نظام تحويل فواتير اتصالات</p></div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="main-header"><h1>📊 Hawelha Telecom</h1><p>احترافي • سريع • دقيق</p></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("ارفع ملف الفاتورة PDF", type=['pdf'])

if uploaded_file:
    if st.button("🚀 استخراج البيانات وتصحيح الأعمدة"):
        with st.spinner("جاري المعالجة الذكية..."):
            records, lang = process_etisalat_pdf(uploaded_file)
            
            if records:
                df = pd.DataFrame(records)
                st.success(f"✅ تم اكتشاف اللغة: {'العربية (يمين لليسار)' if lang == 'arabic' else 'الإنجليزية'}")
                
                # إحصائيات
                c1, c2 = st.columns(2)
                c1.metric("عدد الخطوط", len(df))
                c2.metric("إجمالي الفاتورة", f"{df['إجمالي'].sum():,.2f} ج.م")
                
                st.dataframe(df, use_container_width=True)
                
                excel_file = save_to_excel(df, lang)
                st.download_button(
                    label="📥 تحميل ملف Excel المنظم",
                    data=excel_file,
                    file_name=f"Hawelha_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("لم نتمكن من العثور على جداول بيانات في الملف.")
