import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# ✅ ✅ GLOBAL STYLE (PREMIUM LOOK)
st.markdown("""
    <style>
    .block-container {padding-top: 1rem;}
    h1 {text-align: center;}
    .metric-card {
        background-color:#f5f7fa;
        padding:15px;
        border-radius:10px;
        text-align:center;
        border:1px solid #e6e6e6;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Executive Closure Dashboard")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

# ✅ PDF FUNCTION (same working version)
def create_pdf(data):

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(150, 750, "Closure Dashboard Report")

    total_amt = int(data['Amount - USD'].sum())
    open_items = len(data[data['Closure Status']=="Open"])

    pdf.drawString(50, 720, f"Total Spend: ${total_amt}")
    pdf.drawString(50, 705, f"Open Items: {open_items}")

    # Charts
    temp = data.copy()
    temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
    monthly = temp.groupby("Month")["Amount - USD"].sum()

    plt.figure(figsize=(6,3))
    monthly.plot()
    plt.tight_layout()
    plt.savefig("trend.png")
    plt.close()

    pdf.drawImage("trend.png", 50, 500, width=500, height=200)

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


# ✅ MAIN LOGIC
if uploaded_file:

    df = pd.read_csv(uploaded_file)

    df.columns = df.columns.str.strip()
    df['Spoc'] = df['Spoc'].astype(str).str.strip()
    df['Closure Status'] = df['Closure Status'].astype(str).str.strip()
    df['Division'] = df['Division'].astype(str).str.strip()
    df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

    # ✅ FILTER BAR
    st.markdown("### 🔎 Filters")
    f1, f2, f3 = st.columns(3)

    with f1:
        spoc = st.selectbox("SPOC", ["All"] + sorted(df['Spoc'].unique()))
    with f2:
        status = st.selectbox("Status", ["All"] + sorted(df['Closure Status'].unique()))
    with f3:
        division = st.selectbox("Division", ["All"] + sorted(df['Division'].unique()))

    filtered = df.copy()

    if spoc != "All":
        filtered = filtered[filtered['Spoc'] == spoc]
    if status != "All":
        filtered = filtered[filtered['Closure Status'] == status]
    if division != "All":
        filtered = filtered[filtered['Division'] == division]

    # ✅ KPI SECTION (STYLED)
    st.markdown("### 📌 Key Metrics")

    total_amt = filtered['Amount - USD'].sum()
    open_items = len(filtered[filtered['Closure Status']=="Open"])
    total_items = len(filtered)

    overdue = filtered[
        (filtered['Closure Status']=="Open") &
        (filtered['End Date'] < pd.Timestamp.today())
    ]

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("💰 Total Spend", f"${int(total_amt):,}")
    k2.metric("📦 Total Items", total_items)
    k3.metric("⏳ Open Items", open_items)
    k4.metric("⚠ Overdue", len(overdue))

    # ✅ DIVISION CARDS
    st.markdown("### 💰 Spend by Division")

    div_sum = filtered.groupby("Division")["Amount - USD"].sum().sort_values(ascending=False)

    cols = st.columns(len(div_sum))
    for i, (d, val) in enumerate(div_sum.items()):
        cols[i].metric(d, f"${int(val):,}")

    # ✅ CHART SECTION
    st.markdown("### 📊 Insights")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Monthly Spend")
        temp = filtered.copy()
        temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
        monthly = temp.groupby("Month")["Amount - USD"].sum()
        st.line_chart(monthly)

    with c2:
        st.subheader("📊 Division Spend")
        st.bar_chart(div_sum)

    # ✅ TABLE
    st.markdown("### 📋 Activity Details")

    def highlight(row):
        if row['Closure Status']=="Open" and row['End Date'] < pd.Timestamp.today():
            return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)

    st.dataframe(filtered.style.apply(highlight, axis=1), use_container_width=True)

