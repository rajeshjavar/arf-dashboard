import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(layout="wide")

st.title("📊 Executive Closure Dashboard")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])


# ✅ PDF
def create_pdf(data):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.drawString(200, 750, "Closure Dashboard Report")
    pdf.save()
    buffer.seek(0)
    return buffer


# ✅ MAIN
if uploaded_file is not None:

    try:
        df = pd.read_csv(uploaded_file)

        st.success("✅ File Loaded")

        # ✅ Show columns for debugging
        st.write("Columns:", df.columns.tolist())

        # ✅ Clean headers
        df.columns = df.columns.str.strip()

        # ✅ Required columns
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

        ch1, ch2 = st.columns(2)

        with ch1:
            temp = filtered.copy()
            temp['Month'] = temp['End Date'].dt.to_period("M").astype(str)
            monthly = temp.groupby("Month")["Amount - USD"].sum()
            st.line_chart(monthly)

        with ch2:
            div_sum = filtered.groupby("Division")["Amount - USD"].sum()
            st.bar_chart(div_sum)

        # ✅ TABLE
        st.subheader("📋 Data")
        st.dataframe(filtered, use_container_width=True)

        # ✅ ACTIONS
        st.subheader("📄 Actions")

        colA, colB = st.columns(2)

        # ✅ PDF
        with colA:
            pdf = create_pdf(filtered)
            st.download_button(
                "📥 Download PDF",
                pdf,
                file_name="report.pdf"
            )

        # ✅ EMAIL
        with colB:
            if st.button("📧 Open Outlook Email"):

                pending = filtered[filtered['Closure Status']=="Open"]

                if pending.empty:
                    st.warning("No pending items")
                else:
                    table = ""

                    headers = ["Spoc","Activity","End Date","Amount","Status","Division"]
                    table += "{:<15} {:<10} {:<12} {:<12} {:<10} {:<10}\n".format(*headers)
                    table += "-"*70 + "\n"

                    for _, r in pending.iterrows():
                        table += "{:<15} {:<10} {:<12} {:<12} {:<10} {:<10}\n".format(
                            str(r["Spoc"])[:15],
                            str(r["Activity"]),
                            str(r["End Date"].date()) if pd.notnull(r["End Date"]) else "",
                            int(r["Amount - USD"]),
                            str(r["Closure Status"]),
                            str(r["Division"])
                        )

                    msg = f"Pending Closures Report\n\n{table}"

                    link = f"mailto:?subject={urllib.parse.quote('Pending Closures')}&body={urllib.parse.quote(msg)}"

                    st.link_button("📧 Click to open Outlook", link)

    except Exception as e:
        st.error(f"❌ ERROR OCCURRED: {e}")
``
