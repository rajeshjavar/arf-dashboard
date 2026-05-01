import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(layout="wide")

st.title("📊 Closure & Aging Dashboard")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    # ✅ Cleaning
    df.columns = df.columns.str.strip()
    df['Spoc'] = df['Spoc'].astype(str).str.strip()
    df['Closure Status'] = df['Closure Status'].astype(str).str.strip()
    df['Division'] = df['Division'].astype(str).str.strip()
    df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

    # ✅ FILTER BAR
    f1, f2, f3 = st.columns(3)

    with f1:
        spoc = st.selectbox("SPOC", ["All"] + sorted(df['Spoc'].unique()))
    with f2:
        status = st.selectbox("Status", ["All"] + sorted(df['Closure Status'].unique()))
    with f3:
        division = st.selectbox("Division", ["All"] + sorted(df['Division'].unique()))

    # ✅ FILTER LOGIC
    filtered = df.copy()

    if spoc != "All":
        filtered = filtered[filtered['Spoc'] == spoc]
    if status != "All":
        filtered = filtered[filtered['Closure Status'] == status]
    if division != "All":
        filtered = filtered[filtered['Division'] == division]

    # ✅ KPI CARDS
    total_spend = filtered['Amount - USD'].sum()
    open_items = len(filtered[filtered['Closure Status']=="Open"])
    total_items = len(filtered)

    overdue = filtered[
        (filtered['Closure Status']=="Open") &
        (filtered['End Date'] < pd.Timestamp.today())
    ]

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("💰 Total Spend", f"${int(total_spend):,}")
    k2.metric("📦 Total Items", total_items)
    k3.metric("⏳ Open Items", open_items)
    k4.metric("⚠️ Overdue", len(overdue))

    # ✅ DIVISION CARDS
    st.subheader("💰 Spend by Division")

    div_sum = filtered.groupby("Division")["Amount - USD"].sum().sort_values(ascending=False)

    cols = st.columns(len(div_sum))

    for i, (d, val) in enumerate(div_sum.items()):
        cols[i].metric(d, f"${int(val):,}")

    # ✅ CHARTS
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Monthly Spend Trend")
        df_temp = filtered.copy()
        df_temp['Month'] = df_temp['End Date'].dt.to_period("M").astype(str)
        monthly = df_temp.groupby("Month")["Amount - USD"].sum()
        st.line_chart(monthly)

    with c2:
        st.subheader("📊 Division Spend")
        st.bar_chart(div_sum)

    # ✅ TABLE
    st.subheader("📋 Activity Details")
    st.dataframe(filtered, use_container_width=True)

    # ✅ EMAIL SECTION
    st.subheader("📧 Action")

    if st.button("Send Outlook Reminder"):

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
                    "Download Attachment",
                    csv,
                    file_name=f"{spoc}_pending.csv"
                )

                # formatted text
                header = f"{'Spoc':<18}{'Activity':<12}{'End Date':<15}{'Amount':<10}{'Division'}\n"
                table = header + "-"*70 + "\n"

                for _, row in pending.iterrows():
                    table += f"{row['Spoc']:<18}{row['Activity']:<12}{str(row['End Date'].date()):<15}{int(row['Amount - USD']):<10}{row['Division']}\n"

                msg = f"Pending closures for {spoc}\n\n{table}"

                link = f"mailto:?subject={urllib.parse.quote('Pending Closures')}&body={urllib.parse.quote(msg)}"

                st.markdown(f"{link}")
