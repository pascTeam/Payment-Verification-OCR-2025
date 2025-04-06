# Payment-Verification-OCR-2025
This repository contains a Python script for automating payment verification using Optical Character Recognition (OCR). The script efficiently extracts and validates key payment details from receipts or transaction records.

## Features

- Extracts transaction IDs using **PaddleOCR** from payment screenshots.
- Supports popular platforms like **PhonePe**, **Google Pay**, and **Paytm**.
- Automatically matches extracted transaction IDs with backend transaction logs (Excel/CSV).
- Marks registrations as "verified" or "not verified".
- Generates a clean, downloadable Excel report of verified users.

## Tech Stacks

- Python
- PaddleOCR 
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

## How It Works

1. Upload the registration Excel file.
2. The script:
   - Downloads each screenshot.
   - Applies OCR to extract transaction info.
   - Matches it with backend transaction logs.
3. Generates a final report with verification status.

Payment-Verification-OCR-2025/
├── Transaction verification.ipynb
├── README.md
└── sample_data/
    ├── reg-data.csv
    ├── final transactions.xlsx
    └── Second Transactions for ACM drive.xlsx
