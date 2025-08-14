# app.py
import streamlit as st
import pandas as pd
import os
import extraction  # <-- ADDED IMPORT
import ID_verify   # <-- ADDED IMPORT

st.set_page_config(layout="centered", page_title="Payment Verification OCR")

st.title("Payment Verification OCR")
st.write(
    "Upload your registration data and transaction reports to automatically verify payments."
)

# --- File Uploaders ---
uploaded_csv = st.file_uploader(
    "Upload User Registration CSV (input.csv)", type=["csv"]
)
uploaded_pdfs = st.file_uploader(
    "Upload Transaction Reports (TransactionReport.pdf)",
    type=["pdf"],
    accept_multiple_files=True,
)

if st.button("Start Verification Process"):
    if uploaded_csv is not None and uploaded_pdfs:
        with st.spinner("Processing files... Please wait."):
            try:
                # Save uploaded files to be processed by the scripts
                with open("input.csv", "wb") as f:
                    f.write(uploaded_csv.getbuffer())

                # For simplicity, the verification script looks for one PDF.
                # We'll save the first uploaded PDF with the required name.
                if uploaded_pdfs:
                    first_pdf = uploaded_pdfs[0]
                    with open("TransactionReport.pdf", "wb") as f:
                        f.write(first_pdf.getbuffer())

                # Run the main pipeline
                st.write("Starting extraction of transaction IDs...")
                extraction.main()
                st.write("Extraction complete. Starting ID verification...")
                ID_verify.main()
                st.write("Verification complete.")

                # --- Display and Download Results ---
                st.success("Verification process completed successfully!")

                if os.path.exists("verified_transactions.csv"):
                    # Provide the result for download
                    with open("verified_transactions.csv", "rb") as file:
                        st.download_button(
                            label="Download Verified Transactions",
                            data=file,
                            file_name="verified_transactions.csv",
                            mime="text/csv",
                        )
                    # Display the dataframe in the app as well
                    st.write("### Verification Results")
                    df = pd.read_csv("verified_transactions.csv")
                    st.dataframe(df)
                else:
                    st.error(
                        "The output file 'verified_transactions.csv' was not generated."
                    )

            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload both the CSV and at least one PDF file.")

