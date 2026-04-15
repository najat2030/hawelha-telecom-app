import streamlit as st
import pdfplumber

st.set_page_config(layout="wide")

st.title("Test App")

file = st.file_uploader("Upload PDF", type=["pdf"])

if file:
    st.success("File uploaded")

    try:
        with pdfplumber.open(file) as pdf:
            st.write(f"عدد الصفحات: {len(pdf.pages)}")
            text = pdf.pages[0].extract_text()
            st.write(text[:500] if text else "No text")
    except Exception as e:
        st.error(f"Error: {e}")
