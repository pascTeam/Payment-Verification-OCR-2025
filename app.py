# app.py
import streamlit as st
import pandas as pd
import os
import extraction
import ID_verify
from datetime import datetime
import time
import numpy as np # Added for dummy image in YOLO model testing

# Page configuration
st.set_page_config(
    page_title="Payment Verification OCR",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .upload-section {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #dee2e6;
        margin: 1rem 0;
    }
    
    .status-box {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3e0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ff9800;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #ffebee;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #f44336;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .file-uploader {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>💰 Payment Verification OCR System</h1>
    <p>Automated payment verification using AI-powered OCR and transaction matching</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for navigation and info
with st.sidebar:
    st.markdown("### 📋 Navigation")
    page = st.selectbox(
        "Choose a section:",
        ["🏠 Main Dashboard", "📊 Results", "ℹ️ About"]
    )
    
    st.markdown("---")
    st.markdown("### 📈 System Status")
    
    # Check if model file exists
    model_exists = os.path.exists("model.pt")
    if model_exists:
        try:
            # Try to load the model to test if it works
            from ultralytics import YOLO
            test_model = YOLO("model.pt")
            dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
            test_model.predict(dummy_img, verbose=False)
            st.success("✅ YOLO Model Ready")
        except Exception as e:
            error_msg = str(e)
            if "'AAttn' object has no attribute 'qkv'" in error_msg:
                st.warning("⚠️ YOLO Model has compatibility issues")
                st.caption("Will use fallback OCR automatically")
            else:
                st.warning("⚠️ YOLO Model may have compatibility issues")
                st.caption(f"Error: {error_msg[:50]}...")
    else:
        st.info("ℹ️ No YOLO Model - Will use fallback OCR")
    
    st.markdown("---")
    st.markdown("### 🛠️ Supported Platforms")
    st.markdown("- **PhonePe**: UTR numbers")
    st.markdown("- **Google Pay**: Transaction IDs")
    st.markdown("- **Paytm**: Reference numbers")
    st.markdown("- **Amazon Pay**: Bank Reference IDs")

# Main dashboard
if page == "🏠 Main Dashboard":
    # File upload section
    st.markdown("## 📁 Upload Files")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Registration Data")
        uploaded_csv = st.file_uploader(
            "Upload User Registration CSV",
            type=["csv"],
            help="Upload the CSV file containing user registration data with screenshot URLs"
        )
        
        if uploaded_csv is not None:
            st.success(f"✅ Uploaded: {uploaded_csv.name}")
            # Show preview
            try:
                df_preview = pd.read_csv(uploaded_csv)
                st.markdown("**Preview of uploaded data:**")
                st.dataframe(df_preview.head(), use_container_width=True)
            except:
                st.warning("Could not preview CSV file")
    
    with col2:
        st.markdown("### Transaction Reports")
        uploaded_pdfs = st.file_uploader(
            "Upload Transaction Reports",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload PDF files containing transaction reports to verify against"
        )
        
        if uploaded_pdfs:
            st.success(f"✅ Uploaded {len(uploaded_pdfs)} PDF file(s)")
            for pdf in uploaded_pdfs:
                st.write(f"📄 {pdf.name}")
    
    with col3:
        st.markdown("### YOLO Model (Optional)")
        uploaded_model = st.file_uploader(
            "Upload YOLO Model",
            type=["pt", "pth"],
            help="Upload your trained YOLO model for transaction ID detection (optional - will use fallback OCR if not provided)"
        )
        
        if uploaded_model is not None:
            st.success(f"✅ Uploaded: {uploaded_model.name}")
            # Test the model
            try:
                from ultralytics import YOLO
                # Save the uploaded model temporarily
                with open("temp_model.pt", "wb") as f:
                    f.write(uploaded_model.getbuffer())
                
                # Test the model
                test_model = YOLO("temp_model.pt")
                dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
                test_model.predict(dummy_img, verbose=False)
                st.success("✅ Model loaded successfully")
                
                # Clean up temp file
                if os.path.exists("temp_model.pt"):
                    os.remove("temp_model.pt")
                    
            except Exception as e:
                error_msg = str(e)
                if "'AAttn' object has no attribute 'qkv'" in error_msg:
                    st.warning("⚠️ Model has compatibility issues with current ultralytics version")
                    st.info("ℹ️ System will automatically use fallback OCR method")
                else:
                    st.warning(f"⚠️ Model may have compatibility issues: {error_msg[:50]}...")
                
                # Clean up temp file
                if os.path.exists("temp_model.pt"):
                    os.remove("temp_model.pt")
        else:
            st.info("ℹ️ No model uploaded - will use fallback OCR method")

    # Process button
    st.markdown("---")
    st.markdown("## 🔄 Start Verification Process")
    
    if st.button("🚀 Start Verification", type="primary", use_container_width=True):
        if uploaded_csv is not None and uploaded_pdfs:
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Save files
                status_text.text("📁 Saving uploaded files...")
                progress_bar.progress(10)
                
                with open("input.csv", "wb") as f:
                    f.write(uploaded_csv.getbuffer())
                
                if uploaded_pdfs:
                    first_pdf = uploaded_pdfs[0]
                    with open("TransactionReport.pdf", "wb") as f:
                        f.write(first_pdf.getbuffer())
                
                # Save model if uploaded
                if uploaded_model is not None:
                    with open("model.pt", "wb") as f:
                        f.write(uploaded_model.getbuffer())
                    status_text.text("🤖 YOLO model saved and ready for use")
                else:
                    # Remove any existing model file to use fallback
                    if os.path.exists("model.pt"):
                        os.remove("model.pt")
                    status_text.text("📝 Using fallback OCR method (no YOLO model)")
                
                progress_bar.progress(20)
                
                # Step 2: Extract transaction IDs
                status_text.text("🔍 Extracting transaction IDs from screenshots...")
                progress_bar.progress(40)
                
                extraction.main()
                
                # Step 3: Verify IDs
                status_text.text("✅ Verifying transaction IDs...")
                progress_bar.progress(70)
                
                ID_verify.main()
                
                # Step 4: Complete
                status_text.text("🎉 Verification process completed!")
                progress_bar.progress(100)
                
                st.success("✅ Verification process completed successfully!")
                
                # Display results
                if os.path.exists("verified_transactions.csv"):
                    st.markdown("## 📊 Verification Results")
                    
                    # Load and display results
                    df_results = pd.read_csv("verified_transactions.csv")
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_records = len(df_results)
                        st.metric("Total Records", total_records)
                    
                    with col2:
                        verified_count = len(df_results[df_results['Verification'] == 'Verified'])
                        st.metric("Verified", verified_count)
                    
                    with col3:
                        not_verified_count = len(df_results[df_results['Verification'] == 'Not Verified'])
                        st.metric("Not Verified", not_verified_count)
                    
                    with col4:
                        no_id_count = len(df_results[df_results['Verification'] == 'No ID extracted'])
                        st.metric("No ID Extracted", no_id_count)
                    
                    # Results table
                    st.markdown("### Detailed Results")
                    st.dataframe(df_results, use_container_width=True)
                    
                    # Download button
                    with open("verified_transactions.csv", "rb") as file:
                        st.download_button(
                            label="📥 Download Results (CSV)",
                            data=file,
                            file_name=f"verified_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                else:
                    st.error("❌ The output file 'verified_transactions.csv' was not generated.")
                    
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.exception(e)
        else:
            st.warning("⚠️ Please upload both the CSV and at least one PDF file to proceed.")

elif page == "📊 Results":
    st.markdown("## 📊 Previous Results")
    
    if os.path.exists("verified_transactions.csv"):
        df_results = pd.read_csv("verified_transactions.csv")
        
        # Summary statistics
        st.markdown("### 📈 Summary Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            verified_pct = (len(df_results[df_results['Verification'] == 'Verified']) / len(df_results)) * 100
            st.metric("Verification Rate", f"{verified_pct:.1f}%")
        
        with col2:
            total_records = len(df_results)
            st.metric("Total Records", total_records)
        
        with col3:
            verified_count = len(df_results[df_results['Verification'] == 'Verified'])
            st.metric("Successfully Verified", verified_count)
        
        # Filter options
        st.markdown("### 🔍 Filter Results")
        filter_option = st.selectbox(
            "Filter by verification status:",
            ["All", "Verified", "Not Verified", "No ID extracted"]
        )
        
        if filter_option != "All":
            filtered_df = df_results[df_results['Verification'] == filter_option]
        else:
            filtered_df = df_results
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download filtered results
        if filter_option != "All":
            csv_data = filtered_df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download {filter_option} Results",
                data=csv_data,
                file_name=f"{filter_option.lower().replace(' ', '_')}_results.csv",
                mime="text/csv"
            )
    else:
        st.info("📝 No previous results found. Run the verification process first.")

elif page == "ℹ️ About":
    st.markdown("## ℹ️ About Payment Verification OCR")
    
    st.markdown("""
    ### 🎯 Purpose
    This system automates the verification of payment transactions using advanced OCR (Optical Character Recognition) 
    and AI-powered object detection to extract and validate transaction IDs from payment screenshots.
    
    ### 🔧 How It Works
    1. **Upload Registration Data**: CSV file containing user information and screenshot URLs
    2. **Upload Transaction Reports**: PDF files with official transaction records
    3. **Upload YOLO Model** (Optional): Your trained YOLO model for transaction ID detection
    4. **AI Processing**: 
       - Downloads screenshots from URLs
       - Uses YOLO model to detect transaction ID regions (if provided)
       - Falls back to full-image OCR if no model is provided
       - Extracts transaction IDs using OCR
    5. **Verification**: Matches extracted IDs with official transaction records
    6. **Results**: Generates comprehensive verification report
    
    ### 🛠️ Technology Stack
    - **Python**: Core programming language
    - **YOLOv12**: Object detection for cropping relevant regions
    - **pytesseract**: OCR for text extraction
    - **Streamlit**: Web interface
    - **Pandas**: Data processing
    - **OpenCV**: Image processing
    
    ### 📋 Supported Payment Platforms
    - **PhonePe**: UTR numbers (T + 21 digits)
    - **Google Pay**: Transaction IDs (e.g., AXIS1234567890)
    - **Paytm**: Reference numbers (12-15 digits)
    - **Amazon Pay**: Bank Reference IDs
    
    ### 📁 File Requirements
    - **Input CSV**: Must contain 'screenshots' column with image URLs
    - **Transaction PDF**: Official transaction reports for verification
    - **YOLO Model** (Optional): Trained YOLO model (.pt or .pth format) for transaction ID detection
    """)
    
    # System information
    st.markdown("### 💻 System Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Required Files:**")
        model_exists = os.path.exists("model.pt")
        st.write(f"YOLO Model: {'✅ Present' if model_exists else '❌ Missing'}")
        
        if os.path.exists("input.csv"):
            st.write("Input CSV: ✅ Present")
        else:
            st.write("Input CSV: ❌ Not uploaded")
            
        if os.path.exists("TransactionReport.pdf"):
            st.write("Transaction PDF: ✅ Present")
        else:
            st.write("Transaction PDF: ❌ Not uploaded")
    
    with col2:
        st.markdown("**Output Files:**")
        if os.path.exists("verified_transactions.csv"):
            st.write("Results CSV: ✅ Generated")
        else:
            st.write("Results CSV: ❌ Not generated")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 1rem;'>"
    "Payment Verification OCR System | Built with Streamlit and AI"
    "</div>",
    unsafe_allow_html=True
)

