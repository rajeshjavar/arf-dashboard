import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ✅ ✅ PREMIUM UI STYLE
st.markdown("""
<style>
.block-container {padding-top: 1rem;}
h1 {text-align: center; color: #1f4e79;}

div[data-testid="metric-container"] {
    background-color: #f0f4f8;
    border: 1px solid #e0e0e0;
    padding: 12px;
    border-radius: 10px;
}

button[kind="secondary"] {
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)

