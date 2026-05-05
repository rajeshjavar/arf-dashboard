import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("📊 Executive Closure Dashboard")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

# ✅ PDF FUNCTION
def create_pdf(data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(150, 750, "Closure Dashboard Report")

    total_amt = int(data['Amount - USD'].sum())
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 720, f"Total Spend: ${total_amt}")

    # ✅ Monthly Chart
    temp = data.copy()
    temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
    monthly = temp.groupby("Month")["Amount - USD"].sum()

    plt.figure(figsize=(6,3))
    monthly.plot(marker='o')
    plt.tight_layout()
    plt.savefig("trend.png")
    plt.close()
    pdf.drawImage("trend.png", 50, 500, width=500, height=200)

    # ✅ Division Chart
    div_sum = data.groupby("Division")["Amount - USD"].sum()

    plt.figure(figsize=(6,3))
    div_sum.plot(kind='bar')
    plt.tight_layout()
    plt.savefig("div.png")
    plt.close()
    pdf.drawImage("div.png", 50, 270, width=500, height=200)

    pdf.save()
    buffer.seek(0)
    return buffer


# ✅ MAIN APP (WITH ERROR VISIBILITY)
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # ✅ DEBUG (IMPORTANT)
        st.write("✅ File loaded")
        st.write("Columns detected:", df.columns.tolist())

        # ✅ REQUIRED COLUMNS CHECK
        required = ['Spoc','Activity','End Date','Amount - USD','Closure Status','Division']
        missing = [c for c in required if c not in df.columns]

        if missing:
            st.error(f"❌ Missing columns: {missing}")
            st.stop()

        # ✅ CLEAN
        df.columns = df.columns.str.strip()
        df['Spoc'] = df['Spoc'].astype(str).str.strip()
        df['Closure Status'] = df['Closure Status'].astype(str).str.strip()
        df['Division'] = df['Division'].astype(str).str.strip()
        df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

        # ✅ FILTERS
        st.subheader("🔎 Filters")
        f1, f2, f3 = st.columns(3)

        with f1:
            spoc = st.selectbox("SPOC", ["All"] + sorted(df['Spoc'].dropna().unique()))
        with f2:
            status = st.selectbox("Status", ["All"] + sorted(df['Closure Status'].dropna().unique()))
        with f3:
            division = st.selectbox("Division", ["All"] + sorted(df['Division'].dropna().unique()))

        filtered = df.copy()

        if spoc != "All":
            filtered = filtered[filtered['Spoc'] == spoc]
        if status != "All":
            filtered = filtered[filtered['Closure Status'] == status]
        if division != "All":
            filtered = filtered[filtered['Division'] == division]

        # ✅ KPIs
        st.subheader("📌 KPIs")

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Items", len(filtered))
        k2.metric("Open Items", len(filtered[filtered['Closure Status']=="Open"]))
        k3.metric("Total USD", int(filtered['Amount - USD'].sum()))

        # ✅ CHARTS
        st.subheader("📊 Charts")

        c1, c2 = st.columns(2)

        with c1:
            temp = filtered.copy()
            temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
            monthly = temp.groupby("Month")["Amount - USD"].sum()
            st.line_chart(monthly)

        with c2:
            div_sum = filtered.groupby("Division")["Amount - USD"].sum()
            st.bar_chart(div_sum)

        # ✅ TABLE
        st.subheader("📋 Data")
        st.dataframe(filtered)

