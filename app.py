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
            padding: 2.5rem 2rem;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(5,150,105,0.3);
        }
        
        .logo-container { 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            margin-bottom: 1.5rem;
        }
        
        .logo-img { 
            max-width: 220px; 
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
            padding: 2.5rem 2rem;
            margin-top: 3rem;
            border-radius: 10px;
        }

        .developer-name {
            font-size: 1.8rem; /* مكبر كما طلبت */
            font-weight: 700;
            color: #10b981;
            margin: 0;
            letter-spacing: 0.5px;
        }

        .copyright {
            font-size: 0.9rem;
            opacity: 0.8;
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
                <img class="logo-img" src="data:image/png;base64,{logo}" alt="Logo">
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
                records = extract_etisalat_data(file)  # Assuming this function is defined above
                
                if records:
                    progress_bar.progress(50)
                    
                    df = pd.DataFrame(records)
                    columns_order = [
                        'محمول', 'رسوم شهرية', 'رسوم الخدمات',
                        'مكالمات محلية', 'رسائل محلية', 'إنترنت محلية',
                        'مكالمات دولية', 'رسائل دولية',
                        'مكالمات تجوال', 'رسائل تجوال', 'إنترنت تجوال',
                        'رسوم وتسويات اخري', 'قيمة الضرائب', 'إجمالي'
                    ]
                    df = df[columns_order]
                    progress_bar.progress(80)
                    
                    show_dashboard(df)
                    
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
