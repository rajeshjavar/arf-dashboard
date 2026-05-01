import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(layout="wide")

st.title("📊 Executive Closure Dashboard")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # ✅ Clean data
    df.columns = df.columns.str.strip()
    df['Spoc'] = df['Spoc'].astype(str).str.strip()
    df['Closure Status'] = df['Closure Status'].astype(str).str.strip()
    df['Division'] = df['Division'].astype(str).str.strip()
    df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

    # ✅ FILTERS
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

    # ✅ ✅ KPI SECTION
    total = len(filtered)
    open_items = len(filtered[filtered['Closure Status']=="Open"])
    total_amt = filtered['Amount - USD'].sum()

    overdue = filtered[
        (filtered['Closure Status']=="Open") &
        (filtered['End Date'] < pd.Timestamp.today())
    ]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Spend", f"${int(total_amt):,}")
    k2.metric("📦 Total Items", total)
    k3.metric("⏳ Open Items", open_items)
    k4.metric("⚠ Overdue", len(overdue))

    # ✅ ✅ AGING BUCKETS (NEW)
    st.subheader("⏳ Aging Buckets")

    aging_df = filtered.copy()
    aging_df['Days'] = (pd.Timestamp.today() - aging_df['End Date']).dt.days

    bucket_30 = len(aging_df[(aging_df['Days'] <= 30) & (aging_df['Closure Status']=="Open")])
    bucket_60 = len(aging_df[(aging_df['Days'] > 30) & (aging_df['Days'] <= 60)])
    bucket_60_plus = len(aging_df[(aging_df['Days'] > 60)])

    a1, a2, a3 = st.columns(3)
    a1.metric("0–30 Days", bucket_30)
    a2.metric("31–60 Days", bucket_60)
    a3.metric("60+ Days", bucket_60_plus)

    # ✅ DIVISION CARDS
    st.subheader("💰 Spend by Division")

    div_sum = filtered.groupby("Division")["Amount - USD"].sum().sort_values(ascending=False)

    cols = st.columns(len(div_sum))
    for i, (d, val) in enumerate(div_sum.items()):
        cols[i].metric(d, f"${int(val):,}")

    # ✅ CHARTS
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Monthly Trend")
        temp = filtered.copy()
        temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
        monthly = temp.groupby("Month")["Amount - USD"].sum()
        st.line_chart(monthly)

    with c2:
        st.subheader("📊 Division Spend")
        st.bar_chart(div_sum)

    # ✅ TABLE WITH OVERDUE HIGHLIGHT
    st.subheader("📋 Activity Table")

    def highlight_row(row):
        if row['Closure Status']=="Open" and row['End Date'] < pd.Timestamp.today():
            return ['background-color: red'] * len(row)
        return [''] * len(row)

    st.dataframe(filtered.style.apply(highlight_row, axis=1), use_container_width=True)

    # ✅ ✅ PDF EXPORT (EXECUTIVE REPORT)
    st.subheader("📄 Export")

    def create_pdf(data):
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        p.drawString(50, 750, "Closure Dashboard Report")

        y = 720
        for _, row in data.head(20).iterrows():
            text = f"{row['Spoc']} | {row['Activity']} | {row['End Date'].date()} | {int(row['Amount - USD'])} | {row['Division']}"
            p.drawString(50, y, text)
            y -= 20

        p.save()
        buffer.seek(0)
        return buffer

    pdf = create_pdf(filtered)

    st.download_button(
        "📥 Download PDF Report",
        pdf,
        file_name="closure_report.pdf",
        mime="application/pdf"
    )

    # ✅ EMAIL SECTION
    if st.button("📧 Outlook Reminder"):

        if spoc == "All":
            st.warning("Select SPOC")
        else:
            pending = df[
                (df['Spoc'] == spoc) &
                (df['Closure Status'] == "Open")
            ]

            if pending.empty:
                st.success("No pending items")
            else:
                csv = pending.to_csv(index=False)

                st.download_button(
                    "📥 Download Pending CSV",
                    csv,
                    file_name=f"{spoc}_pending.csv"
                )

                msg = f"Pending closures for {spoc}\n\nTotal Amount: ${int(pending['Amount - USD'].sum())}"

                mailto = f"mailto:?subject={urllib.parse.quote('Pending Closures')}&body={urllib.parse.quote(msg)}"

                st.markdown(f"{mailto}")
