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
    3. رسوم
