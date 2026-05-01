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

# ✅ PDF CREATION FUNCTION
def create_pdf(data):

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter

    # ✅ TITLE
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(180, 750, "Closure Dashboard Report")

    # ✅ KPI
    total_amt = int(data['Amount - USD'].sum())
    open_items = len(data[data['Closure Status']=="Open"])
    overdue = len(data[
        (data['Closure Status']=="Open") &
        (data['End Date'] < pd.Timestamp.today())
    ])

    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, 720, f"Total Spend: ${total_amt}")
    pdf.drawString(50, 705, f"Open Items: {open_items}")
    pdf.drawString(50, 690, f"Overdue: {overdue}")

    # ✅ MONTHLY TREND CHART
    temp = data.copy()
    temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
    monthly = temp.groupby("Month")["Amount - USD"].sum()

    plt.figure(figsize=(6,3))
    monthly.plot(marker='o')
    plt.title("Monthly Spend Trend")
    plt.tight_layout()
    plt.savefig("trend.png")
    plt.close()

    pdf.drawImage("trend.png", 50, 480, width=500, height=180)

    # ✅ DIVISION CHART
    div_sum = data.groupby("Division")["Amount - USD"].sum()

    plt.figure(figsize=(6,3))
    div_sum.plot(kind='bar')
    plt.title("Division Spend")
    plt.tight_layout()
    plt.savefig("division.png")
    plt.close()

    pdf.drawImage("division.png", 50, 270, width=500, height=180)

    # ✅ TABLE
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 250, "Top Activities")

    pdf.setFont("Helvetica", 9)

    y = 230
    for _, row in data.head(10).iterrows():
        text = f"{row['Spoc']} | {row['Activity']} | {row['End Date'].date()} | ${int(row['Amount - USD'])} | {row['Division']}"
        pdf.drawString(50, y, text)
        y -= 15

    pdf.save()
    buffer.seek(0)

    return buffer


# ✅ MAIN APP LOGIC
if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # ✅ CLEAN DATA
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

    # ✅ APPLY FILTER
    filtered = df.copy()

    if spoc != "All":
        filtered = filtered[filtered['Spoc'] == spoc]
    if status != "All":
        filtered = filtered[filtered['Closure Status'] == status]
    if division != "All":
        filtered = filtered[filtered['Division'] == division]

    # ✅ KPI SECTION
    total = len(filtered)
    open_items = len(filtered[filtered['Closure Status']=="Open"])
    total_amt = filtered['Amount - USD'].sum()

    overdue_df = filtered[
        (filtered['Closure Status']=="Open") &
        (filtered['End Date'] < pd.Timestamp.today())
    ]

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("💰 Total Spend", f"${int(total_amt):,}")
    k2.metric("📦 Total Items", total)
    k3.metric("⏳ Open Items", open_items)
    k4.metric("⚠ Overdue", len(overdue_df))

    # ✅ AGING BUCKETS
    st.subheader("⏳ Aging Buckets")

    aging = filtered.copy()
    aging['Days'] = (pd.Timestamp.today() - aging['End Date']).dt.days

    a1, a2, a3 = st.columns(3)

    a1.metric("0–30 Days", len(aging[(aging['Days'] <= 30) & (aging['Closure Status']=="Open")]))
    a2.metric("31–60 Days", len(aging[(aging['Days'] > 30) & (aging['Days'] <= 60)]))
    a3.metric("60+ Days", len(aging[(aging['Days'] > 60)]))

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

    # ✅ OVERDUE HIGHLIGHT TABLE
    st.subheader("📋 Activity Table")

    def highlight(row):
        if row['Closure Status']=="Open" and row['End Date'] < pd.Timestamp.today():
            return ['background-color: red'] * len(row)
        return [''] * len(row)

    st.dataframe(filtered.style.apply(highlight, axis=1), use_container_width=True)

    # ✅ PDF DOWNLOAD
    st.subheader("📄 Export")

    pdf = create_pdf(filtered)

    st.download_button(
        "📥 Download Executive PDF",
        pdf,
        file_name="closure_dashboard_report.pdf",
        mime="application/pdf"
    )

    # ✅ EMAIL
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

                link = f"mailto:?subject={urllib.parse.quote('Pending Closures')}&body={urllib.parse.quote(msg)}"

                st.markdown(f"{link}")
