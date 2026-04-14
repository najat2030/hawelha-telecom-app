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
    layout="wide"
)

# ========== CSS مخصص للتنسيق ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    * { font-family: 'Cairo', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: white; padding: 2rem; border-radius: 15px;
        text-align: center; margin-bottom: 2rem;
    }
    .footer {
        background: #1e293b; color: white; text-align: center;
        padding: 1rem; margin-top: 3rem; border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ========== دوال المعالجة المنطقية ==========

def extract_numbers_from_row(row):
    """استخراج الأرقام من الصف مع معالجة الإشارة السالبة والترتيب العربي"""
    found_values = []
    if not row: return found_values

    for cell in row:
        if cell is None: continue
        # تنظيف النص ومعالجة السالب في نهاية الرقم (مثل 10.5-)
        val_str = str(cell).strip().replace(',', '')
        if val_str.endswith('-'):
            val_str = '-' + val_str[:-1]
        
        # البحث عن الأرقام
        nums = re.findall(r'(-?\d+\.?\d*)', val_str)
        for n in nums:
            try:
                found_values.append(float(n))
            except: pass
    return found_values

def parse_etisalat_table(table):
    """معالجة الجدول: الهاتف في صف والمبالغ في الصف التالي"""
    records = []
    if not table: return records
    
    i = 0
    while i < len(table):
        # تحويل الصف لنص للبحث عن رقم الموبايل
        current_row_text = " ".join([str(c) for c in table[i] if c])
        phone_match = re.search(r'(01[0125]\d{8})', current_row_text)
        
        if phone_match:
            phone = phone_match.group(1)
            # المبالغ في الصف التالي (i + 1)
            if i + 1 < len(table):
                next_row = table[i + 1]
                # استخراج الأرقام (تظهر من اليسار لليمين في PDF)
                raw_values = extract_numbers_from_row(next_row)
                
                # عكس الترتيب لأن الجدول RTL (من اليمين لليسار)
                # لكي تصبح "الرسوم الشهرية" هي أول عنصر و"الإجمالي" هو آخر عنصر
                v = raw_values[::-1]
                
                # ملء القيم الناقصة بأصفار لضمان عدم حدوث خطأ
                v = v + [0.0] * (14 - len(v))
                
                record = {
                    'محمول': phone,
                    'رسوم شهرية': v[0],
                    'رسوم الخدمات': v[1],
                    'مكالمات محلية': v[2],
                    'رسائل محلية': v[3],
                    'إنترنت محلية': v[4],
                    'مكالمات دولية': v[5],
                    'رسائل دولية': v[6],
                    'مكالمات تجوال': v[7],
                    'رسائل تجوال': v[8],
                    'إنترنت تجوال': v[9],
                    'رسوم وتسويات اخري': v[10],
                    'قيمة الضرائب': v[11],
                    'إجمالي': v[12] if len(raw_values) > 1 else 0.0
                }
                # تصحيح الإجمالي: غالباً ما يكون هو أول قيمة قرأها الكود (أقصى اليسار)
                if len(raw_values) > 0:
                    record['إجمالي'] = raw_values[0]

                records.append(record)
                i += 2 # تخطي صف المبالغ
            else:
                i += 1
        else:
            i += 1
    return records

# ========== واجهة المستخدم Streamlit ==========

st.markdown('<div class="main-header"><h1>📊 Hawelha Telecom | حوّلها تليكوم</h1><p>استخراج ذكي لفواتير اتصالات المزدوجة</p></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("ارفع ملف الفاتورة PDF (يبدأ الاستخراج من صفحة 3)", type=['pdf'])

if uploaded_file:
    if st.button("🚀 بدء المعالجة الآن"):
        all_records = []
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                # البدء من صفحة 3 (Index 2)
                for page in pdf.pages[2:]:
                    # استخراج الجداول (استخدام استراتيجية النصوص لتحسين الدقة)
                    table = page.extract_table({
                        "vertical_strategy": "text",
                        "horizontal_strategy": "text"
                    })
                    if table:
                        all_records.extend(parse_etisalat_table(table))
            
            if all_records:
                df = pd.DataFrame(all_records)
                # ترتيب الأعمدة
                cols = ['محمول', 'رسوم شهرية', 'رسوم الخدمات', 'مكالمات محلية', 'رسائل محلية', 
                        'إنترنت محلية', 'مكالمات دولية', 'رسائل دولية', 'مكالمات تجوال', 
                        'رسائل تجوال', 'إنترنت تجوال', 'رسوم وتسويات اخري', 'قيمة الضرائب', 'إجمالي']
                df = df[cols]
                
                st.success(f"✅ تم استخراج {len(df)} سجل بنجاح!")
                st.dataframe(df, use_container_width=True)
                
                # تحويل إلى Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Data')
                
                st.download_button(
                    label="📥 تحميل ملف Excel",
                    data=output.getvalue(),
                    file_name=f"Telecom_Extract_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ لم يتم العثور على بيانات في الصفحات المحددة.")
        except Exception as e:
            st.error(f"❌ حدث خطأ: {e}")

st.markdown('<div class="footer"><p>Hawelha Telecom © 2026 - نظام استخراج البيانات المتقدم</p></div>', unsafe_allow_html=True)
