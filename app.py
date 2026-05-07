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

    required = ['Spoc','Activity','End Date','Amount - USD','Closure Status','Division']
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"❌ Missing columns: {missing}")
        st.stop()

    df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

    # ✅ FILTERS
    st.subheader("🔎 Filters")

    col1, col2, col3 = st.columns(3)

    spoc = col1.selectbox("SPOC", ["All"] + sorted(df['Spoc'].dropna().unique()))
    status = col2.selectbox("Status", ["All"] + sorted(df['Closure Status'].dropna().unique()))
    division = col3.selectbox("Division", ["All"] + sorted(df['Division'].dropna().unique()))

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

    temp = filtered.copy()
    temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
    monthly = temp.groupby("Month")["Amount - USD"].sum()
    c1.line_chart(monthly)

    div_sum = filtered.groupby("Division")["Amount - USD"].sum()
    c2.bar_chart(div_sum)

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

    # ✅ ✅ ✅ HTML EMAIL TABLE (FINAL PREMIUM VERSION)
 with a2:
    pending = filtered[filtered['Closure Status'] == "Open"]

    if pending.empty:
        st.warning("No pending items")
    else:
        email_df = pending[[
            "Spoc","Activity","End Date","Amount - USD","Closure Status","Division"
        ]].copy()

        email_df["End Date"] = email_df["End Date"].dt.date

        # ✅ HTML table
        html_table = email_df.to_html(index=False)

        html_table = html_table.replace(
            "<table",
            "<table border='1' style='border-collapse:collapse;'"
        )

        html_body = f"""
        <html>
        <body>
        <h3>Pending Closures Report</h3>
        {html_table}
        </body>
        </html>
        """

        # ✅ CREATE EML FILE
        eml_content = f"""Subject: Pending Closures
Content-Type: text/html

{html_body}
"""

        st.download_button(
            "📧 Download Outlook Email (Ready Format)",
            eml_content,
            file_name="pending_closures.eml",
            mime="message/rfc822"
        )
