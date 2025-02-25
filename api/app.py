from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime
import cv2
from services.ocr import base64_to_cv2_img, extract_odometer_reading
import traceback
from database import Database
from middlewares.auth import require_auth

# Load environment variables
load_dotenv()

app = Flask(__name__)
db = Database()

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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Only admins can create admin users
    role = data.get('role', 'user')
    if role == 'admin':
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Admin creation requires authentication'}), 401
        
        token = auth_header.split(' ')[1]
        user = db.verify_session(token)
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Only admins can create admin users'}), 403

    success = db.create_user(
        username=data['username'],
        password=data['password'],
        role=role
    )
    
    if not success:
        return jsonify({'error': 'Username already exists'}), 409
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = db.verify_user(data['username'], data['password'])
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = db.create_session(user['id'])
    
    return jsonify({
        'token': token,
        'role': user['role']
    })

@app.route('/odometer', methods=['POST'])
@require_auth(roles=['admin', 'user'])
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