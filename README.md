# Payment-Verification-OCR-2025
This repository contains a Python script for automating payment verification using Optical Character Recognition (OCR) and object detection. The script efficiently extracts and validates key payment details from receipts or transaction records.

## Features

- Extracts transaction IDs from payment screenshots using **YOLOv12** for cropping and **pytesseract** for OCR.
- Supports popular platforms like **PhonePe**, **Google Pay**.
- Automatically matches extracted transaction IDs with backend transaction logs (Excel/CSV).
- Marks registrations as "verified" or "not verified".
- Generates a clean, downloadable Excel report of verified users.

## Tech Stacks

- Python
- YOLOv12 (object detection for cropping relevant regions)
- pytesseract (OCR)
- Pandas
- Regex (for robust ID extraction)
- Google Colab / Jupyter compatible

## Input Files

1. `reg-data.csv` – User registration data with screenshot links.
2. `final transactions.xlsx` – Drive log of successful transactions.
3. `Second Transactions for ACM drive.xlsx` – Additional transaction logs.

## Output

- A downloadable Excel file containing:
  - Name
  - Extracted transaction ID
  - Status (Verified / Not Verified)

## Supported Receipt Types

- **PhonePe**: UTR numbers starting with `T` followed by 21 digits.
- **Google Pay**: Transaction IDs like `AXIS1234567890`.
- **Paytm**: 12 to 15 digit numeric transaction reference numbers.
- **Amazon Pay**: Bank Reference Id (alphanumeric, typically labeled as 'Bank Reference Id').

## How It Works

1. Upload the registration Excel file.
2. The script:
   - Downloads each screenshot.
   - Uses YOLOv12 to detect and crop the transaction ID region.
   - Applies pytesseract OCR to extract transaction info.
   - Matches it with backend transaction logs.
3. Generates a final report with verification status.

Payment-Verification-OCR-2025/
├── Transaction_verification_YOLO .ipynb
├── model.pt
├── README.md
└── sample_data/
    ├── reg-data.csv
    ├── final transactions.xlsx
    └── Second Transactions for ACM drive.xlsx
