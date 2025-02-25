import easyocr
import cv2
import numpy as np
import base64
import traceback

def base64_to_cv2_img(base64_string):
    """Convert base64 string to OpenCV image"""
    try:
        # Remove data:image/jpeg;base64, prefix if it exists
        if 'base64,' in base64_string:
            base64_string = base64_string.split('base64,')[1]
        
        # Decode base64 string to bytes
        img_bytes = base64.b64decode(base64_string)
        
        # Convert bytes to numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        
        # Decode numpy array as image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return img
    except Exception as e:
        print(f"Error converting base64 to image: {str(e)}")
        return None

def validate_reading(reading, user_reading):
    """Validate OCR reading against user input"""
    try:
        if not reading:
            return False
        
        # Convert both to strings for comparison
        reading_str = str(reading)
        user_reading_str = str(user_reading)
        
        print(f"Validating - OCR: {reading_str} vs User: {user_reading_str}")
        
        # Basic length check
        if len(reading_str) < 4 or len(reading_str) > 8:
            print(f"❌ Invalid length: {len(reading_str)}")
            return False
        
        # Check for exact match
        if reading_str == user_reading_str:
            print("✓ Exact match")
            return True
        
        # Check if one contains the other
        if reading_str in user_reading_str or user_reading_str in reading_str:
            print("✓ Partial match")
            return True
        
        # Check if they're similar (allow for small differences)
        if len(reading_str) == len(user_reading_str):
            differences = sum(1 for a, b in zip(reading_str, user_reading_str) if a != b)
            if differences <= 1:  # Allow one digit difference
                print("✓ Similar match (one digit difference)")
                return True
        
        print("❌ No match")
        return False
        
    except Exception as e:
        print(f"Error in reading validation: {str(e)}")
        return False

def extract_odometer_reading(image, user_reading):
    """Extract odometer reading using EasyOCR"""
    try:
        print("\n=== Starting EasyOCR Process ===")
        print(f"User reading: {user_reading}")
        
        # Initialize EasyOCR reader (only numbers)
        reader = easyocr.Reader(['en'], gpu=True)  # Set gpu=False if no GPU available
        
        # Get results
        results = reader.readtext(image, allowlist='0123456789')
        
        print(f"Raw EasyOCR results: {results}")
        
        # Extract all number sequences
        readings = []
        for detection in results:
            bbox, text, conf = detection
            digits = ''.join(filter(str.isdigit, text))
            if digits:
                readings.append((digits, conf))
                print(f"Found reading: {digits} (confidence: {conf:.2f})")
        
        if not readings:
            print("No readings found")
            return None
        
        # Sort by confidence
        readings.sort(key=lambda x: x[1], reverse=True)
        
        # Validate readings against user input
        user_reading_str = str(user_reading)
        
        for reading, conf in readings:
            if validate_reading(reading, user_reading):
                print(f"✓ Valid reading found: {reading} (confidence: {conf:.2f})")
                return reading
        
        # If no valid reading found, return the highest confidence reading
        print(f"! No valid reading found, using highest confidence: {readings[0][0]}")
        return readings[0][0]
        
    except Exception as e:
        print(f"Error in EasyOCR processing: {str(e)}")
        traceback.print_exc()
        return None