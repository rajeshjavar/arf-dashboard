import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

    # ✅ Validate columns
    required = ['Spoc','Activity','End Date','Amount - USD','Closure Status','Division']
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"❌ Missing columns: {missing}")
        st.stop()

    # ✅ Format date
    df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

    # ✅ FILTERS
    st.subheader("🔎 Filters")

    c1, c2, c3 = st.columns(3)

    spoc = c1.selectbox("SPOC", ["All"] + sorted(df['Spoc'].dropna().unique()))
    status = c2.selectbox("Status", ["All"] + sorted(df['Closure Status'].dropna().unique()))
    division = c3.selectbox("Division", ["All"] + sorted(df['Division'].dropna().unique()))

    # ✅ APPLY FILTER
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

    col1, col2 = st.columns(2)

    # Monthly trend
    temp = filtered.copy()
    temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
    monthly = temp.groupby("Month")["Amount - USD"].sum()

    col1.line_chart(monthly)

    # Division spend
    div_sum = filtered.groupby("Division")["Amount - USD"].sum()
    col2.bar_chart(div_sum)

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

    # ✅ ✅ EMAIL (FINAL CLEAN TABLE VERSION)
    with a2:
        if st.button("📧 Open Outlook Email"):

            pending = filtered[filtered['Closure Status'] == "Open"]

            if pending.empty:
                st.warning("No pending items")
            else:
                # ✅ structured table using pandas
                email_df = pending[[
                    "Spoc","Activity","End Date","Amount - USD","Closure Status","Division"
                ]].copy()

                email_df["End Date"] = email_df["End Date"].dt.date

                table = email_df.to_string(index=False)

                msg = f"Pending Closures Report\n\n{table}"

                subject = urllib.parse.quote(f"Pending Closures - {len(pending)} items")
                body = urllib.parse.quote(msg)

                link = f"mailto:?subject={subject}&body={body}"

                st.link_button("📧 Click to open Outlook", link)
