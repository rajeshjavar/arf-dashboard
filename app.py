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

    # Monthly chart
    temp = data.copy()
    temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
    monthly = temp.groupby("Month")["Amount - USD"].sum()

    plt.figure(figsize=(6,3))
    monthly.plot(marker='o')
    plt.tight_layout()
    plt.savefig("trend.png")
    plt.close()

    pdf.drawImage("trend.png", 50, 500, width=500, height=200)

    # Division chart
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


# ✅ MAIN APP
if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    # ✅ CLEAN HEADERS
    df.columns = df.columns.str.strip()

    # ✅ CHECK REQUIRED COLUMNS
    required = ['Spoc','Activity','End Date','Amount - USD','Closure Status','Division']
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"❌ Missing columns: {missing}")
        st.stop()

    # ✅ FORMAT
    df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

    # ✅ FILTERS
    st.subheader("🔎 Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        spoc = st.selectbox("SPOC", ["All"] + sorted(df['Spoc'].dropna().unique()))

    with col2:
        status = st.selectbox("Status", ["All"] + sorted(df['Closure Status'].dropna().unique()))

    with col3:
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

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Total Items", len(filtered))
    k2.metric("Open Items", len(filtered[filtered['Closure Status']=="Open"]))
    k3.metric("Total USD", int(filtered['Amount - USD'].sum()))

    overdue = filtered[
        (filtered['Closure Status']=="Open") &
        (filtered['End Date'] < pd.Timestamp.today())
    ]

    k4.metric("Overdue", len(overdue))

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
    st.dataframe(filtered, use_container_width=True)

    # ✅ ACTIONS
    st.subheader("📄 Actions")

    colA, colB = st.columns(2)

    # ✅ PDF BUTTON
    with colA:
        pdf = create_pdf(filtered)

        st.download_button(
            label="📥 Download PDF",
            data=pdf,
            file_name="closure_dashboard_report.pdf",
            mime="application/pdf"
        )

    # ✅ OUTLOOK BUTTON (SAFE VERSION — NO BREAK)
    with colB:
        if st.button("📧 Open Outlook Email"):

            msg = "Pending closures report"
            link = f"mailto:?subject=Closures&body={urllib.parse.quote(msg)}"

          st.link_button("📧 Click here to open Outlook", link)
