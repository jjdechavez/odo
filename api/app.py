from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io
import os
import base64
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
import easyocr
from collections import Counter
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": os.getenv('CORS_ORIGINS', '').split(','),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure app from environment variables
app.config.update(
    UPLOAD_FOLDER=os.getenv('UPLOAD_FOLDER', 'uploads'),
    MAX_CONTENT_LENGTH=int(os.getenv('MAX_CONTENT_LENGTH', 2097152)),  # Default 2MB
    ENV=os.getenv('FLASK_ENV', 'production'),
    DEBUG=os.getenv('FLASK_DEBUG', '0') == '1'
)

def base64_to_cv2_img(base64_string):
    """Convert base64 string to OpenCV image"""
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/odometer', methods=['POST'])
def upload_odometer():
    """Upload odometer image with user reading"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        if 'user_odometer' not in data:
            return jsonify({'error': 'user_odometer is required'}), 400
        
        try:
            user_odometer = int(data['user_odometer'])
        except ValueError:
            return jsonify({'error': 'user_odometer must be a valid integer'}), 400
        
        # Convert base64 to image
        image = base64_to_cv2_img(data['image'])
        if image is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"odometer_{timestamp}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save original image
        cv2.imwrite(filepath, image)
        print(f"\n=== Starting New OCR Request ===")
        print(f"Original image saved: {filepath}")
        print(f"User odometer reading: {user_odometer}")
        
        # Extract reading using OCR
        ocr_reading = extract_odometer_reading(image, user_odometer)
        
        if not ocr_reading:
            ocr_reading = "Failed to extract reading"
            print("❌ OCR failed to extract reading")
        else:
            print(f"✓ Successfully extracted OCR reading: {ocr_reading}")
        
        response_data = {
            'success': True,
            'data': {
                'user_reading': user_odometer,
                'ocr_reading': ocr_reading,
                'timestamp': datetime.now().isoformat(),
                'filename': filename
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in upload_odometer: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large',
        'max_size': app.config['MAX_CONTENT_LENGTH']
    }), 413

if __name__ == '__main__':
    app.run(
        host=os.getenv('API_HOST', '0.0.0.0'),
        port=int(os.getenv('API_PORT', 5000)),
        debug=app.config['DEBUG']
    )