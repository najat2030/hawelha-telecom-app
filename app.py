import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import os
import gc
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="Hawelha Telecom", layout="wide", page_icon="📊")

# ================= STYLE & THEME =================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
.stApp { background-color: #f8f9fa; font-family: 'Tajawal', sans-serif; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
.login-background { position: fixed; inset: 0; background-color: #F4F6F8; z-index: -1; }
.login-card { background: rgba(255, 255, 255, 0.97); padding: 35px 30px; border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); border: 1px solid rgba(255, 255, 255, 0.4); max-width: 430px; margin: 70px auto; text-align: center; }
.login-title { color: #1a7e43; font-size: 26px; font-weight: 800; margin-bottom: 20px; }
.royal-green-box, div.stButton > button { background-color: #1a7e43 !important; color: white !important; border-radius: 50px !important; border: 2px solid #146435 !important; font-family: 'Segoe UI', sans-serif; font-weight: 600 !important; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; margin: 0 !important; }
.royal-green-box { min-height: 45px !important; width: fit-content !important; padding: 5px 16px !important; font-size: 14px !important; gap: 8px !important; margin-left: auto !important; }
div.stButton > button { min-height: 45px !important; width: 100% !important; font-size: 14px !important; }
.avatar-circle-white { background-color: white !important; color: #1a7e43 !important; border-radius: 50%; width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-left: 8px; }
.header-container { background: white; padding: 10px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; text-align: center; }
.header-logo { width: 100% !important; max-width: 650px !important; height: auto; }
.metric-card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); border-right: 5px solid #1a7e43; margin-bottom: 10px; text-align: center; }
.metric-title { font-size: 18px !important; color: #555; font-weight: 600 !important; }
.metric-value { font-size: 32px !important; color: #1a7e43; font-weight: 800 !important; }
.stProgress > div > div > div > div { background-color: #daa520 !important; }
</style>
""", unsafe_allow_html=True)

# ================= USERS DATA =================
def load_users():
    try:
        df_users = pd.read_excel("users.xlsx")
        return {str(row["Username"]).strip(): str(row["Password"]).strip() for _, row in df_users.iterrows()}
    except:
        return {"admin": "123"}

users = load_users()

# ================= SESSION STATE =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-card"><div class="login-title">🔐 تسجيل الدخول</div></div>', unsafe_allow_html=True)
        u = st.text_input("Username", placeholder="اسم المستخدم", label_visibility="collapsed")
        p = st.text_input("Password", placeholder="كلمة المرور", type="password", label_visibility="collapsed")
        if st.button("دخول"):
            if u.strip() in users and users[u.strip()] == p.strip():
                st.session_state.logged_in = True
                st.session_state.username = u.strip()
                st.rerun()
            else:
                st.error("❌ خطأ في اسم المستخدم أو كلمة المرور")
    st.stop()

# ================= HEADER =================
logo_url = "https://raw.githubusercontent.com/najat2030/hawelha-telecom-app/main/static/logo.png"
col_out, col_logo, col_me = st.columns([1, 4, 1], vertical_alignment="center")
with col_out:
    if st.button("🚪 خروج"):
        st.session_state.logged_in = False
        st.rerun()
with col_logo:
    st.markdown(f'<div class="header-container"><img src="{logo_url}" class="header-logo"></div>', unsafe_allow_html=True)
with col_me:
    initial = st.session_state.username[0].upper()
    st.markdown(f'<div class="royal-green-box"><span class="avatar-circle-white">{initial}</span>مرحباً، {st.session_state.username}</div>', unsafe_allow_html=True)

# ================= HELPER FUNCTIONS =================
def normalize(t):
    """توحيد علامات الطرح والأقواس"""
    return (t or "").replace("−", "-").replace("–", "-").replace("—", "-")

def extract_numbers_with_position(text, phone):
    """
    استخراج الأرقام مع مراعاة الترتيب الصحيح للفواتير العربية (RTL)
    وإزالة رقم الموبايل من القائمة
    """
    if not text:
        return []
    
    text = normalize(str(text))
    # تحويل الأقواس لقيم سالبة: (7.12) -> -7.12
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    
    # استخراج الأرقام مع مواضعها في النص
    matches = []
    for match in re.finditer(r'-?\d+(?:\.\d+)?', text):
        num = float(match.group())
        # استبعاد رقم الموبايل
        if str(int(abs(num))) != phone[:10] and abs(num) > 0.01:
            matches.append((match.start(), num))
    
    # ترتيب حسب الموضع في النص (مهم للجداول العربية)
    matches.sort(key=lambda x: x[0])
    return [num for _, num in matches]

def build_record_smart(values, phone):
    """
    بناء سجل ذكي يضع القيم السالبة في عمود 'رسوم تسويات' أولاً
    ثم يوزع باقي القيم على الأعمدة بالترتيب
    """
    columns_order = [
        "رسوم شهرية", "رسوم الخدمات", "مكالمات محلية", "رسائل محلية", 
        "إنترنت محلية", "مكالمات دولية", "رسائل دولية", "مكالمات تجوال", 
        "رسائل تجوال", "إنترنت تجوال", "رسوم تسويات", "ضرائب", "إجمالي"
    ]
    
    # عزل القيم السالبة (مرشحة للتسويات)
    negatives = [v for v in values if v < 0]
    positives = [v for v in values if v >= 0]
    
    record = {"محمول": phone}
    
    # 1️⃣ أولاً: نضع القيمة السالبة في "رسوم تسويات" إذا وجدت
    if negatives:
        record["رسوم تسويات"] = negatives[0]
        remaining_values = positives + negatives[1:]  # باقي القيم
    else:
        record["رسوم تسويات"] = 0.0
        remaining_values = positives
    
    # 2️⃣ نوزع باقي القيم على الأعمدة الأخرى بالترتيب
    val_idx = 0
    for col in columns_order:
        if col in record:  # تم ملؤه مسبقاً
            continue
        if val_idx < len(remaining_values):
            record[col] = remaining_values[val_idx]
            val_idx += 1
        else:
            record[col] = 0.0
    
    return record

def validate_record(record):
    """تحقق بسيط من منطقية القيم المستخرجة"""
    try:
        total = abs(record.get("إجمالي", 0))
        components = [
            abs(record.get("رسوم شهرية", 0)),
            abs(record.get("رسوم الخدمات", 0)),
            abs(record.get("مكالمات محلية", 0)),
            abs(record.get("رسائل محلية", 0)),
            abs(record.get("إنترنت محلية", 0)),
            abs(record.get("مكالمات دولية", 0)),
            abs(record.get("رسائل دولية", 0)),
            abs(record.get("مكالمات تجوال", 0)),
            abs(record.get("رسائل تجوال", 0)),
            abs(record.get("إنترنت تجوال", 0)),
            abs(record.get("رسوم تسويات", 0)),
            abs(record.get("ضرائب", 0))
        ]
        expected = sum(components)
        # هامش خطأ 5 جنيهات مقبول
        return abs(total - expected) <= 5
    except:
        return False

def parse_file_improved(file, is_arabic):
    """الدالة الرئيسية لمعالجة ملفات PDF بدقة عالية"""
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            # نبدأ من الصفحة الثالثة كما في الهيكل الأصلي للفاتورة
            for page in pdf.pages[2:]:
                tables = page.extract_tables()
                for table in tables or []:
                    for row_idx, row in enumerate(table):
                        if not row or not any(row):
                            continue
                        
                        # تجميع نص الصف مع الحفاظ على الترتيب
                        cells = [str(c).strip() for c in row if c is not None]
                        full_text = " ".join(cells)
                        
                        # استخراج رقم الموبايل
                        phone_match = re.search(r'(01[0125]\d{8})', full_text)
                        if not phone_match:
                            continue
                        
                        phone = phone_match.group(1)
                        
                        # استخراج الأرقام بالترتيب الصحيح
                        values = extract_numbers_with_position(full_text, phone)
                        
                        # نحتاج على الأقل 10 قيم لبناء سجل معقول
                        if len(values) < 10:
                            continue
                        
                        # بناء السجل الذكي
                        record = build_record_smart(values, phone)
                        
                        # إضافة علامة تحقق من الجودة
                        record["✓ تم التحقق"] = "نعم" if validate_record(record) else "مراجعة"
                        
                        records.append(record)
                        
    except Exception as e:
        st.error(f"⚠️ خطأ في معالجة الملف: {str(e)}")
    
    return records

# ================= UI & MAIN LOGIC =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)
mode = st.radio("إعدادات اللغة", ["Auto 🤖", "عربي 🇪🇬", "English 🇺🇸"], horizontal=True)

if st.button("🚀 بدء المعالجة والتحليل", type="primary"):
    if not files:
        st.warning("⚠️ من فضلك اختر ملفاً واحداً على الأقل")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_data = []
        
        for idx, file in enumerate(files):
            status_text.text(f"🔄 جاري معالجة: {file.name} ...")
            file.seek(0)
            
            # تحديد اللغة تلقائياً أو يدوياً
            if mode == "Auto 🤖":
                try:
                    with pdfplumber.open(file) as pdf:
                        first_page_text = pdf.pages[0].extract_text() or ""
                    is_ar = bool(re.search(r'[\u0600-\u06FF]', first_page_text))
                except:
                    is_ar = True  # الافتراضي عربي
            else:
                is_ar = (mode == "عربي 🇪🇬")
            
            file.seek(0)
            data = parse_file_improved(file, is_ar)
            all_data.extend(data)
            
            # تحديث شريط التقدم
            progress_bar.progress((idx + 1) / len(files))
            gc.collect()
        
        status_text.empty()
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # 📊 عرض الملخص المالي
            st.markdown("### 📈 ملخص التحليل المالي")
            m1, m2, m3, m4, m5 = st.columns(5)
            
            with m1:
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-title">📱 إجمالي الخطوط</div>
                    <div class="metric-value">{len(df):,}</div>
                </div>''', unsafe_allow_html=True)
            
            with m2:
                monthly_sum = df["رسوم شهرية"].sum()
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-title">💰 الرسوم الشهرية</div>
                    <div class="metric-value">{monthly_sum:,.2f} ج.م</div>
                </div>''', unsafe_allow_html=True)
            
            with m3:
                settlements_sum = df["رسوم تسويات"].sum()
                color = "red" if settlements_sum < 0 else "#1a7e43"
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-title">🧾 صافي التسويات</div>
                    <div class="metric-value" style="color: {color};">{settlements_sum:,.2f} ج.م</div>
                </div>''', unsafe_allow_html=True)
            
            with m4:
                taxes_sum = df["ضرائب"].sum()
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-title">🏛️ إجمالي الضرائب</div>
                    <div class="metric-value">{taxes_sum:,.2f} ج.م</div>
                </div>''', unsafe_allow_html=True)
            
            with m5:
                total_sum = df["إجمالي"].sum()
                st.markdown(f'''
                <div class="metric-card">
                    <div class="metric-title">💎 الإجمالي النهائي</div>
                    <div class="metric-value">{total_sum:,.2f} ج.م</div>
                </div>''', unsafe_allow_html=True)
            
            # 🔍 فلاتر عرض البيانات
            col_filt1, col_filt2 = st.columns(2)
            with col_filt1:
                show_only_verified = st.checkbox("✅ عرض الصفوف المُتحقق منها فقط", value=False)
            with col_filt2:
                search_phone = st.text_input("🔍 بحث برقم الموبايل", placeholder="اكتب جزء من الرقم...")
            
            # تطبيق الفلاتر
            display_df = df.copy()
            if show_only_verified:
                display_df = display_df[display_df["✓ تم التحقق"] == "نعم"]
            if search_phone:
                display_df = display_df[display_df["محمول"].str.contains(search_phone, na=False)]
            
            # عرض الجدول
            st.markdown("### 📋 تفاصيل البيانات المستخرجة")
            st.dataframe(
                display_df, 
                use_container_width=True,
                column_config={
                    "محمول": st.column_config.TextColumn("📱 المحمول", width="medium"),
                    "إجمالي": st.column_config.NumberColumn("💰 الإجمالي", format="%.2f"),
                    "✓ تم التحقق": st.column_config.TextColumn("الحالة", width="small")
                }
            )
            
            # 📥 أزرار التصدير
            col_exp1, col_exp2 = st.columns(2)
            
            # تصدير Excel
            with col_exp1:
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="تقرير الفواتير")
                st.download_button(
                    "📥 تحميل تقرير Excel", 
                    data=excel_buf.getvalue(), 
                    file_name=f"Hawelha_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # تصدير CSV
            with col_exp2:
                csv_buf = io.BytesIO()
                df.to_csv(csv_buf, index=False, encoding='utf-8-sig')
                st.download_button(
                    "📄 تحميل كـ CSV", 
                    data=csv_buf.getvalue(), 
                    file_name=f"Hawelha_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            # 📝 ملاحظة جودة البيانات
            unverified_count = len(df[df["✓ تم التحقق"] != "نعم"])
            if unverified_count > 0:
                st.info(f"💡 ملاحظة: هناك {unverified_count} صف يحتاج مراجعة يدوية بسبب اختلاف بسيط في المجموع")
        
        else:
            st.warning("⚠️ لم يتم استخراج أي بيانات. تأكد من أن ملفات PDF تحتوي على جداول بالفواتير من الصفحة الثالثة فصاعداً.")

# ================= FOOTER =================
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666; font-size: 12px; padding: 10px;">© 2026 Hawelha Telecom | جميع الحقوق محفوظة</div>', unsafe_allow_html=True)
