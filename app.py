# ================= FILE UPLOAD & PROCESSING =================
files = st.file_uploader("📂 رفع ملفات PDF", type=["pdf"], accept_multiple_files=True)

if files:
    if st.button("🚀 بدء المعالجة والتحليل", use_container_width=True):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_data = []

        for idx, file in enumerate(files):
            status_text.text(f"⏳ جاري معالجة: {file.name}")
            progress_bar.progress((idx+1)/len(files))

            # Logic Selection
            if mode == "English 🌍":
                data = parse_en(file)

            elif mode == "Auto 🤖":
                data = parse_ar(file)

                if not data:
                    data = parse_en(file)

                if not data:
                    data = parse_ai(file)

            else:  # Arabic
                data = parse_ar(file)
                
            # Fallback
            if not data:
                data = parse_ai(file)

            all_data.extend(data)
            gc.collect()

        progress_bar.progress(100)
        status_text.empty()

        if all_data:
            df_result = pd.DataFrame(all_data)
            
            # Calculations
            total_lines = len(df_result)
            sum_monthly = df_result["رسوم شهرية"].sum()
            sum_settlements = df_result["رسوم تسويات"].sum()
            sum_taxes = df_result["ضرائب"].sum()
            sum_total = df_result["إجمالي"].sum()

            def fmt_curr(val):
                return f"{val:,.0f} ج.م"

            st.markdown("<br>", unsafe_allow_html=True)
            
            # ================= DASHBOARD =================
            st.markdown("### 📈 ملخص التحليل المالي")
            
            m1, m2, m3, m4, m5 = st.columns(5)
            
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">📱 إجمالي الخطوط</div>
                    <div class="metric-value">{total_lines}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with m2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">💰 الرسوم الشهرية</div>
                    <div class="metric-value">{fmt_curr(sum_monthly)}</div>
                </div>
                """, unsafe_allow_html=True)

            with m3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🧾 رسوم التسويات</div>
                    <div class="metric-value">{fmt_curr(sum_settlements)}</div>
                </div>
                """, unsafe_allow_html=True)

            with m4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">🏛️ إجمالي الضرائب</div>
                    <div class="metric-value">{fmt_curr(sum_taxes)}</div>
                </div>
                """, unsafe_allow_html=True)

            with m5:
                st.markdown(f"""
                <div class="metric-card" style="border-right-color: #004d40;">
                    <div class="metric-title">💎 الإجمالي الكلي</div>
                    <div class="metric-value" style="color:#004d40;">{fmt_curr(sum_total)}</div>
                </div>
                """, unsafe_allow_html=True)

            st.success("✅ تم الانتهاء من معالجة الملفات بنجاح!")
            
            st.markdown("---")
            st.markdown("### 📋 تفاصيل البيانات")
            st.dataframe(df_result, use_container_width=True, hide_index=True)

            st.download_button(
                label="📥 تحميل تقرير Excel",
                data=to_excel(df_result),
                file_name="Nagat_Telecom_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.error("❌ لم يتم استخراج بيانات من الملفات")
