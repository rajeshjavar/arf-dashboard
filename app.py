import streamlit as st
import pandas as pd
import urllib.parse

st.title("📊 Closure & Aging Dashboard")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        df.columns = df.columns.str.strip()

        required = ['Spoc','Activity','End Date','Amount - USD','Closure Status','Division']
        missing = [c for c in required if c not in df.columns]

        if missing:
            st.error(f"❌ Missing columns: {missing}")
            st.stop()

        df['Spoc'] = df['Spoc'].astype(str).str.strip()
        df['Closure Status'] = df['Closure Status'].astype(str).str.strip()
        df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')

        spoc = st.selectbox("Select SPOC", ["All"] + sorted(df['Spoc'].unique()))
        status = st.selectbox("Closure Status", ["All"] + sorted(df['Closure Status'].unique()))

        filtered = df.copy()

        if spoc != "All":
            filtered = filtered[filtered['Spoc'] == spoc]

        if status != "All":
            filtered = filtered[filtered['Closure Status'] == status]

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Items", len(filtered))
        col2.metric("Open Items", len(filtered[filtered['Closure Status'] == "Open"]))
        col3.metric("Total USD", int(filtered['Amount - USD'].sum()))

        overdue = filtered[
            (filtered['Closure Status'] == "Open") &
            (filtered['End Date'] < pd.Timestamp.today())
        ]

        col4.metric("Overdue", len(overdue))

        st.subheader("📋 Activity Details")
        st.dataframe(filtered, use_container_width=True)

        if st.button("📧 Outlook Email + Attachment"):

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
                    pending_csv = pending.to_csv(index=False)

                    st.download_button(
                        "📥 Download Attachment",
                        pending_csv,
                        file_name=f"{spoc}_pending.csv",
                        mime="text/csv"
                    )

                    header = f"{'Spoc':<18}{'Activity':<12}{'End Date':<15}{'Amount':<10}{'Division'}\n"
                    line = "-" * 70 + "\n"

                    table = header + line

                    for _, row in pending.iterrows():
                        table += (
                            f"{row['Spoc']:<18}"
                            f"{str(row['Activity']):<12}"
                            f"{str(row['End Date'].date()):<15}"
                            f"{int(row['Amount - USD']):<10}"
                            f"{row['Division']}\n"
                        )

                    message = f"Pending closures for {spoc}\n\n{table}"

                    body = urllib.parse.quote(message)
                    subject = urllib.parse.quote(f"Pending Closures - {spoc}")

                    mailto = f"mailto:?subject={subject}&body={body}"

                    st.markdown(f"[📧 Click here to open Outlook Email]({mailto})")

    except Exception as e:
        st.error(f"Error: {e}")
