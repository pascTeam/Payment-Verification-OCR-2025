# Imports
import cv2
import numpy as np
import re
import pytesseract
import requests
import pandas as pd
import os
import warnings
import traceback

# Suppress warnings that might cause issues
warnings.filterwarnings('ignore')

# --- IMP: Set the paths of the following properly
# Include the code to choose yolo model here
MODEL_PATH = "model.pt"
INPUT_PATH = "input.csv"  # or .xlsx
# Input format:
# column : "screenshots" with all screenshot URLs
OUTPUT_PATH = "processed_transactions.csv"  # or .xlsx
# ---

# Global model variable
model = None
use_yolo = False

def load_yolo_model():
    """
    Safely loads the YOLO model with comprehensive error handling.
    Returns False if YOLO cannot be used, True if successful.
    """
    global model, use_yolo
    
    # Check if model file exists
    if not os.path.exists(MODEL_PATH):
        print("No YOLO model file found. Using fallback OCR method.")
        use_yolo = False
        return False
    
    try:
        # Import ultralytics only when needed
        from ultralytics import YOLO
        
        # Try to load the model
        model = YOLO(MODEL_PATH)
        
        # Test with a dummy image
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        results = model.predict(dummy_img, verbose=False)
        
        print("✅ YOLO model loaded successfully")
        use_yolo = True
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ YOLO model loading failed: {error_msg}")
        
        # Check for specific compatibility errors
        if "'AAttn' object has no attribute 'qkv'" in error_msg:
            print("⚠️ This is a known compatibility issue with ultralytics versions.")
            print("   Using fallback OCR method without YOLO cropping.")
        elif "CUDA" in error_msg or "GPU" in error_msg:
            print("⚠️ GPU/CUDA issue detected. Using fallback OCR method.")
        else:
            print("⚠️ Unknown YOLO error. Using fallback OCR method.")
        
        model = None
        use_yolo = False
        return False

def find_id_box(img):
    """
    Runs the YOLO model on the input image and returns detected boxes or None.
    Includes comprehensive error handling for the 'AAttn' object error.
    """
    global use_yolo, model
    
    if not use_yolo or model is None:
        return None
    
    try:
        # Run prediction with error handling
        results = model.predict(img, verbose=False)
        
        if not results or len(results) == 0:
            return None
            
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return None
            
        return boxes
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ YOLO prediction failed: {error_msg}")
        
        # If we get the 'AAttn' error during prediction, disable YOLO for future calls
        if "'AAttn' object has no attribute 'qkv'" in error_msg:
            print("⚠️ Disabling YOLO due to compatibility issues. Using fallback OCR.")
            use_yolo = False
            model = None
        
        return None

def crop_image(img):
    """
    Crops the input image to the first detected YOLO bounding box.
    Falls back to full image if no box is detected or YOLO fails.
    """
    try:
        boxes = find_id_box(img)
        if boxes is None:
            print("No YOLO boxes detected, using full image for OCR")
            return img

        # Use the first detected box
        box = boxes.xyxy[0]  # (x1, y1, x2, y2)
        x1, y1, x2, y2 = map(int, box)

        # Ensure coordinates are within image bounds
        h, w = img.shape[:2]
        x1 = max(0, min(x1, w))
        y1 = max(0, min(y1, h))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        
        # Ensure valid crop dimensions
        if x2 <= x1 or y2 <= y1:
            print("Invalid crop dimensions, using full image")
            return img

        # Crop the image
        cropped_img = img[y1:y2, x1:x2]
        return cropped_img
        
    except Exception as e:
        print(f"Error in crop_image: {e}")
        return img


def download_image(image_url):
    """
    Downloads an image from a given URL and returns it as a NumPy array.

    Args:
        image_url (str): URL of the image to download.

    Returns:
        img (np.ndarray or None): Decoded image as a NumPy array, or None if download fails.
    """
    response = requests.get(image_url)
    if response.status_code == 200:
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return None


def process_image_url(image_url):
    """
    Processes an image URL: downloads, crops, runs OCR, and extracts the transaction ID.

    Args:
        image_url (str): URL of the image to process.

    Returns:
        transaction_id (str or None): Extracted transaction ID, or None if extraction fails.
    """
    try:
        if not image_url:
            return None
        image = download_image(image_url)
        if image is not None:
            cropped = crop_image(image)
            if cropped is None:
                return None
            text = pytesseract.image_to_string(cropped)
            extract = extract_transaction_details(text)
            return extract
        return None
    except Exception as e:
        print(f"[ERROR] Failed to process image URL: {image_url}\nException: {e}")
        return None


def extract_transaction_details(text):
    """
    Extracts a 12-digit transaction ID from OCR text.

    Args:
        text (str): OCR-extracted text from the transaction screenshot.

    Returns:
        transaction_id (str or None): 12-digit transaction ID if found, else None.
    """
    lines = text.split("\n")
    transaction_id = None
    print(lines)
    if len(lines) == 2:
        transaction_id = lines[0][-12:]
    elif len(lines) == 3:
        transaction_id = lines[1]
    pattern = r"^\d{12}$"
    if re.match(pattern, transaction_id):
        return transaction_id
    else:
        return None


def process_transactions(reg_path):
    """
    Processes an input CSV/Excel file to extract transaction IDs from screenshots.

    Args:
        reg_path (str): Path to the input CSV or Excel file.

    Returns:
        reg (pd.DataFrame): DataFrame with an added 'extracted_transaction_id' column.
    """
    # Check file extension and read accordingly
    if reg_path.endswith('.xlsx'):
        reg = pd.read_excel(reg_path, dtype=str)
    else:
        reg = pd.read_csv(reg_path, dtype=str)
    
    reg["extracted_transaction_id"] = (
        reg["screenshot"].dropna().apply(process_image_url)
    )
    return reg


def save(df, output_filename="processed_transactions.csv"):
    """
    Saves the processed DataFrame to a CSV or Excel file.

    Args:
        df (pd.DataFrame): DataFrame to save.
        output_filename (str): Output filename (CSV or Excel).
    """
    df["extracted_transaction_id"] = df["extracted_transaction_id"].astype("Int64")
    
    # Save based on file extension
    if output_filename.endswith('.xlsx'):
        df.to_excel(output_filename, index=False)
    else:
        df.to_csv(output_filename, index=False)


def main():
    """
    Main function to handle input, processing, and output.
    """
    # Initialize YOLO model with error handling
    print("🔍 Initializing YOLO model...")
    yolo_success = load_yolo_model()
    
    if yolo_success:
        print("✅ Using YOLO model for transaction ID detection")
    else:
        print("📝 Using fallback OCR method (full image processing)")
    
    # Determine input file path (check both .csv and .xlsx)
    input_path = None
    if os.path.exists("input.xlsx"):
        input_path = "input.xlsx"
    elif os.path.exists("input.csv"):
        input_path = "input.csv"
    else:
        raise FileNotFoundError("No input file found (input.csv or input.xlsx)")
    
    print(f"📁 Using input file: {input_path}")
    
    # Process transactions
    print("🔄 Processing transactions...")
    processed_df = process_transactions(input_path)
    save(processed_df, OUTPUT_PATH)
    print("✅ Transaction processing completed!")


if __name__ == "__main__":
    main()
