# Odometer OCR App

A mobile application that captures odometer readings using OCR (Optical Character Recognition) technology. The app consists of a React Native/Expo mobile frontend and a Flask backend API.

## Project Structure 

├── api/
│   ├── app.py
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── app.js
│   ├── package.json
│   └── README.md
```

## Backend Setup (API)

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Make

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd project/api
```

2. Setup the development environment:
```bash
make setup
```
This command will:
- Create a virtual environment
- Install dependencies
- Create necessary directories
- Create .env file

3. Start the API server:
```bash
make run
```

### Available Make Commands

```bash
make setup      # Initial setup (venv, dependencies, directories)
make install    # Install/update dependencies
make run        # Run the API server
make clean      # Remove virtual environment and cached files
```

### Manual Configuration

The .env file will be created with default values. Update them as needed:
```env
FLASK_ENV=development
FLASK_APP=app.py
FLASK_DEBUG=1
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=png,jpg,jpeg
MAX_CONTENT_LENGTH=2097152
API_PORT=8086
API_HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:8081,exp://192.168.1.2:8081,exp://localhost:8081
```

The API will be available at `http://localhost:8086`

## Mobile App Setup

### Prerequisites
- Node.js 16+
- npm or yarn
- Expo CLI
- Expo Go app on your mobile device

### Installation

1. Navigate to the mobile directory:
```bash
cd project/mobile
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Start the Expo development server:
```bash
npx expo start
```

4. Scan the QR code with your mobile device's camera to open the app in Expo Go

## API Endpoints

### Health Check
```
GET /health
```
Returns the API health status.

### Upload Odometer Reading
```
POST /odometer
Content-Type: application/json

{
    "image": "base64_encoded_image",
    "user_odometer": 123456
}
```

Response:
```json
{
    "success": true,
    "data": {
        "user_reading": 123456,
        "ocr_reading": "123456",
        "timestamp": "2024-03-14T12:34:56.789Z",
        "filename": "odometer_20240314_123456.jpg"
    }
}
```

## Features

- Camera capture of odometer readings
- Gallery image selection
- OCR processing using EasyOCR
- Image validation and processing
- Error handling and validation
- Debug logging

## Technical Details

### Backend (Flask API)
- EasyOCR for text recognition
- OpenCV for image processing
- Flask-CORS for handling cross-origin requests
- Environment configuration using python-dotenv
- File upload handling with size limits (2MB max)

### Mobile (React Native/Expo)
- Camera integration using expo-camera
- Image picker for gallery selection
- Base64 image encoding
- Network request handling
- Error handling and user feedback

## Development Notes

1. For local development, ensure your mobile device and development machine are on the same network

2. Update the API URL in your mobile app to match your local machine's IP address

3. The API saves processed images in the `uploads` directory for debugging

4. Check the API logs for detailed OCR processing information

## Troubleshooting

1. If OCR fails:
   - Ensure good lighting conditions
   - Keep the camera steady
   - Frame only the odometer numbers
   - Check the debug images in uploads folder

2. If connection fails:
   - Verify API is running
   - Check IP address and port
   - Ensure mobile device and API are on same network

3. If image upload fails:
   - Check image size (max 2MB)
   - Verify base64 encoding
   - Check network connectivity