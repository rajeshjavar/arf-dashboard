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

    pdf.save()
    buffer.seek(0)
    return buffer


# ✅ MAIN APP
if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    required = ['Spoc','Activity','End Date','Amount - USD','Closure Status','Division']
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"❌ Missing columns: {missing}")
        st.stop()

    df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

    # ✅ FILTERS
    st.subheader("🔎 Filters")

    c1, c2, c3 = st.columns(3)
    with c1:
        spoc = st.selectbox("SPOC", ["All"] + sorted(df['Spoc'].dropna().unique()))
    with c2:
        status = st.selectbox("Status", ["All"] + sorted(df['Closure Status'].dropna().unique()))
    with c3:
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

    a1, a2 = st.columns(2)

    # ✅ PDF
    with a1:
        pdf = create_pdf(filtered)
        st.download_button(
            "📥 Download PDF",
            pdf,
            file_name="closure_dashboard_report.pdf",
            mime="application/pdf"
        )

    # ✅ ✅ ✅ EMAIL WITH TABLE (FINAL FIX)
    with a2:
        if st.button("📧 Open Outlook Email"):

            pending = filtered[filtered['Closure Status'] == "Open"]

            if pending.empty:
                st.warning("No pending items")
            else:
                # ✅ Create table text
                table = ""

                # ✅ Header row
                headers = ["Spoc","Activity","End Date","Amount - USD","Closure Status","Division"]
                table += "{:<15} {:<10} {:<12} {:<15} {:<15} {:<10}\n".format(*headers)
                table += "-" * 80 + "\n"

                # ✅ Rows
                for _, row in pending.iterrows():
                    table += "{:<15} {:<10} {:<12} {:<15} {:<15} {:<10}\n".format(
                        str(row["Spoc"])[:15],
                        str(row["Activity"]),
                        str(row["End Date"].date()) if pd.notna(row["End Date"]) else "",
                        int(row["Amount - USD"]),
                        str(row["Closure Status"]),
                        str(row["Division"])
                    )

                msg = f"Pending Closures Report\n\n{table}"

                link = f"mailto:?subject={urllib.parse.quote('Pending Closures')}&body={urllib.parse.quote(msg)}"

                st.link_button("📧 Click to open Outlook (Table Format)", link)
``
