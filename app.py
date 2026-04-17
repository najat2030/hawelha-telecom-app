import streamlit as st
import pdfplumber
import pandas as pd
import re
import io
import base64
import os
import gc

# ================= CONFIG =================
st.set_page_config(
    page_title="Hawelha Telecom | حوّلها تليكوم",
    page_icon="📊",
    layout="wide"
)

# ================= MODE =================
mode = st.radio(
    "🌐 اختر وضع التحليل",
    ["Auto 🤖", "عربي 🇪", "English 🌍"],
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

if logo:
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 10px;">
        <img src="image/png;base64,{logo}" width="80%" style="max-width: 1000px;">
    </div>
    """, unsafe_allow_html=True)

# =========================================================
# 🚫🚫 DO NOT MODIFY BELOW THIS LINE (CORE LOGIC) 🚫
# =========================================================

def normalize(t):
    return (t or "").replace("−","-").replace("–","-").replace("—","-")

def extract_numbers(text):
    if not text:
        return []
    text = normalize(str(text))
    text = re.sub(r'\((\d+\.?\d*)\)', r'-\1', text)
    text = re.sub(r'(\d+\.?\d*)-', r'-\1', text)
    text = re.sub(r'-\s+(\d)', r'-\1', text)
    numbers = re.findall(r'-?\d+(?:\.\d+)?', text)
    return [float(n) for n in numbers]

def clean_numbers(vals, phone):
    phone_int = str(int(phone))
    cleaned = []
    for v in vals:
        # منع ظهور رقم الهاتف كقيمة مالية إذا تشابه الرقم
        if str(int(v)) != phone_int and len(str(int(v))) != 11:
            cleaned.append(v)
    return cleaned

def fix_phone(phone):
    phone = str(phone)
    if len(phone) == 10 and phone.startswith("1"):
        return "0" + phone
    return phone

# ================= AR TABLE PARSER =================
def parse_ar(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
            # تخطي الصفحات التحليلية
            page_text = page.extract_text() or ""
            if any(kw in page_text for kw in ["تحليل", "خطط", "أسعار", "رسم بياني"]):
                continue
                
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
                        phone_num = phone.group(1)
                        vals = extract_numbers(text)
                        if i+1 < len(table):
                            nxt = extract_numbers(" ".join([str(c) for c in table[i+1] if c]))
                            if len(nxt) > len(vals):
                                vals = nxt
                                i += 1
                        vals = clean_numbers(vals, phone_num)
                        vals = vals[::-1]
                        def g(i): return vals[i] if i < len(vals) else 0
                        records.append({
                            "محمول": phone_num,
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

# ================= EN TABLE PARSER =================
def parse_en(file):
    records = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages[2:]:
             # تخطي الصفحات التحليلية
            page_text = page.extract_text() or ""
            if any(kw in page_text for kw in ["Analysis", "Plan", "Price", "Chart"]):
                continue

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
                        phone_num = phone.group(1)
                        vals = extract_numbers(" ".join([str(c) for c in table[i+1] if c]) if i+1 < len(table) else "")
                        vals = clean_numbers(vals, phone_num)
                        records.append({
                            "محمول": phone_num,
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

# ================= AI / SINGLE INVOICE PARSER (FIXED) =================
def parse_single_invoice(file):
    """
    مخصص للفواتير الفردية التي لا تحتوي على جداول خطوط متعددة.
    يبحث عن الكلمات المفتاحية في نص الصفحة ويستخرج القيم المرتبطة بها.
    """
    records = []
    try:
        with pdfplumber.open(file) as pdf:
            # نجمع النص من الصفحات الأولى (عادة الملخص يكون في البداية)
            full_text = ""
            for page in pdf.pages[:5]: # نفحص أول 5 صفحات فقط للسرعة
                full_text += normalize(page.extract_text() or "") + "\n"

        # البحث عن رقم المحمول
        phone_match = re.search(r'(01[0125]\d{8}|\b1[0125]\d{8}\b)', full_text)
        if not phone_match:
            return [] # لا يوجد رقم محمول، نتجاهل الملف

        phone = fix_phone(phone_match.group(1))

        # دالة مساعدة للبحث عن قيمة بجانب كلمة مفتاحية
        def get_value(keywords):
            for kw in keywords:
                # نمط البحث: الكلمة المفتاحية متبوعة بمسافات ثم رقم (صحيح أو عشري)
                pattern = rf"{kw}\s*[:\-]?\s*(\d+\.?\d*)"
                match = re.search(pattern, full_text)
                if match:
                    return float(match.group(1))
            return 0.0

        record = {
            "محمول": phone,
            # كلمات مفتاحية شائعة في فواتير اتصالات المصرية
            "رسوم شهرية": get_value(["إجمالي الرسوم الشهرية", "الرسوم الشهرية", "Monthly Charges"]),
            "رسوم الخدمات": get_value(["رسوم الخدمات", "Service Fees"]),
            "مكالمات محلية": get_value(["مكالمات محلية", "Local Calls"]),
            "رسائل محلية": get_value(["رسائل محلية", "Local SMS"]),
            "إنترنت محلية": get_value(["إنترنت محلية", "Local Internet"]),
            "مكالمات دولية": get_value(["مكالمات دولية", "International Calls"]),
            "رسائل دولية": get_value(["رسائل دولية", "International SMS"]),
            "مكالمات تجوال": get_value(["مكالمات تجوال", "Roaming Calls"]),
            "رسائل تجوال": get_value(["رسائل تجوال", "Roaming SMS"]),
            "إنترنت تجوال": get_value(["إنترنت تجوال", "Roaming Data"]),
            "رسوم تسويات": get_value(["تنمية موارد الدولة", "تسويات", "Settlements"]),
            "ضرائب": get_value(["ضريبة", "Tax", "VAT"]),
            "إجمالي": get_value(["إجمالي القيمة المستحقة", "الإجمالي", "Total Amount", "Grand Total"])
        }
        
        # التحقق من أن هناك بيانات مستخرجة غير أصفار (لتجنب إضافة سجل فارغ)
        if any(v != 0 for k, v in record.items() if k != "محمول"):
            records.append(record)

    except Exception as e:
        pass # في حالة أي خطأ، نعود للقائمة الفارغة
        
    return records

# ================= EXCEL =================
def to_excel(df):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    out.seek(0)
    return out

# ================= UI =================
files = st.file_uploader(
    "Upload PDF Files",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed"
)

# ================= MAIN =================
if files:

    if st.button("🚀 Start Processing"):

        progress_bar = st.progress(0)
        status_text = st.empty()

        all_data = []
        failed_files = []
        total_files = len(files)

        for idx, file in enumerate(files):
            try:
                status_text.text(f"📄 Processing: {file.name}")
                progress_bar.progress(int(((idx + 1) / total_files) * 100))

                # تحديد اللغة
                if mode == "Auto 🤖":
                    with pdfplumber.open(file) as pdf:
                        text = pdf.pages[0].extract_text() or ""
                    lang = "ar" if re.search(r'[\u0600-\u06FF]', text) else "en"
                else:
                    lang = "ar" if mode == "عربي 🇪" else "en"

                data = []
                
                # 1. محاولة الاستخراج بالطريقة القياسية (جداول)
                try:
                    data = parse_ar(file) if lang == "ar" else parse_en(file)
                except:
                    data = []

                # 2. إذا فشلت الطريقة القياسية (أو لم تجد بيانات)، نستخدم الطريقة الذكية للفواتير الفردية
                if not data:
                    data = parse_single_invoice(file)

                if data:
                    all_data.extend(data)
                else:
                    failed_files.append(file.name)

            except Exception as e:
                failed_files.append(file.name)
                continue

            gc.collect()

        progress_bar.progress(100)
        status_text.text("✅ اكتملت المعالجة!")

        if all_
            df = pd.DataFrame(all_data)

            total_lines = len(df)
            total_monthly = df["رسوم شهرية"].sum()
            total_settlements = df["رسوم تسويات"].sum()
            total_grand = df["إجمالي"].sum()

            st.markdown("## 📊 Dashboard")

            k1, k2, k3, k4 = st.columns(4)

            with k1:
                st.metric("عدد الخطوط", total_lines)
            with k2:
                st.metric("إجمالي الرسوم الشهرية", f"{total_monthly:,.2f}")
            with k3:
                st.metric("إجمالي التسويات", f"{total_settlements:,.2f}")
            with k4:
                st.metric("الإجمالي النهائي", f"{total_grand:,.2f}")

            st.dataframe(df.head(20), use_container_width=True)

            excel = to_excel(df)

            st.success("🎉 تم التحويل بنجاح")
            st.download_button("📥 تحميل Excel", excel, "hawelha_all_files.xlsx")

            if failed_files:
                st.warning(f"⚠️ فواتير لم يتم استخراج بيانات منها: {len(failed_files)}")
                st.write(failed_files)

        else:
            st.error("No data extracted from any file.")
