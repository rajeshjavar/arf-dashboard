import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ✅ STYLE
st.markdown("""
<style>
.block-container {padding-top: 1rem;}
h1 {text-align:center;}
</style>
""", unsafe_allow_html=True)

st.title("📊 Executive Closure Dashboard")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

