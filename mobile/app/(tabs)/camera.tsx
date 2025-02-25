import React, { useState, useRef } from 'react';
import { StyleSheet, View, TouchableOpacity, Text, Alert, Image, TextInput, Button } from 'react-native';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import { MaterialIcons } from '@expo/vector-icons';
import { ThemedView } from '@/components/ThemedView';

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<CameraType>('back');
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [capturedImageUri, setCapturedImageUri] = useState<string | null>(null);
  const [odometerReading, setOdometerReading] = useState('');
  const cameraRef = useRef<CameraView>(null);

  const pickImage = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 1,
        base64: true,
      });

      console.log('Result:', result);
      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        setCapturedImageUri(asset.uri);
        if (!asset.base64) {
          const response = await fetch(asset.uri);
          const blob = await response.blob();
          const base64 = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => {
              if (typeof reader.result === 'string') {
                resolve(reader.result.split(',')[1]);
              }
            };
            reader.readAsDataURL(blob);
          });
          setCapturedImage(base64 as string);
        } else {
          setCapturedImage(asset.base64);
        }
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image from gallery');
    }
  };

  if (!permission) {
    return <ThemedView />;  
  }
  if (!permission.granted) {
    return <View style={styles.container}>
      <Text>No access to camera</Text>
      <Button title="Grant permission" onPress={requestPermission} />
    </View>;
  }

  async function takePicture() {
    if (cameraRef.current) {
      try {
        const photo = await cameraRef.current.takePictureAsync({
          quality: 1,
          base64: true,
        });

        if (!photo?.base64) {
          Alert.alert('Failed to take picture', 'Please try again');
          return;
        }

        setCapturedImage(photo.base64);
        setCapturedImageUri(photo.uri);
      } catch (error) {
        console.error("Camera error:", error);
        Alert.alert('Error', 'Failed to take picture');
      }
    }
  };

  function handleRetake() {
    setCapturedImage(null);
  };

  async function handleConfirm() {
    try {
      console.log('Captured image:', capturedImage);
      console.log('Odometer reading:', odometerReading);
      const response = await fetch('http://192.168.1.7:8086/odometer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          image: capturedImage,
          user_odometer: odometerReading
        })
      });

      if (!response.ok) {
        throw new Error('Failed to confirm image');
      } 

      Alert.alert('Success', 'Image confirmed!');
    } catch (error) {
      console.error('Error confirming image:', error);
    }
  };

  function toggleCameraFacing() {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  }

  if (capturedImageUri) {
    return (
      <ThemedView style={styles.container}>
        <View style={styles.previewContainer}>
          <Image source={{ uri: capturedImageUri }} style={styles.preview} />
          <TextInput
            style={styles.odometerInput}
            placeholder="Enter odometer reading"
            placeholderTextColor="white"
            value={odometerReading}
            onChangeText={setOdometerReading}
            keyboardType="numeric"
          />
          <View style={styles.confirmationButtons}>
            <TouchableOpacity style={styles.button} onPress={handleRetake}>
              <MaterialIcons name="replay" size={28} color="white" />
              <Text style={styles.buttonText}>Retake</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.button} onPress={handleConfirm}>
              <MaterialIcons name="check" size={28} color="white" />
              <Text style={styles.buttonText}>Confirm</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ThemedView>
    );
  }

  return (
    <ThemedView style={styles.container}>
      <CameraView 
        ref={cameraRef}
        style={styles.camera} 
        facing={facing}
      >
        <View style={styles.overlay}>
          <View style={styles.buttonContainer}>
            <TouchableOpacity style={styles.captureButton} onPress={takePicture}>
              <MaterialIcons name="camera" size={32} color="white" />
            </TouchableOpacity>
          </View>
          <TouchableOpacity 
            style={styles.flipButton} 
            onPress={toggleCameraFacing}
          >
            <MaterialIcons name="flip-camera-ios" size={28} color="white" />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.galleryButton} 
            onPress={pickImage}
          >
            <MaterialIcons name="photo-library" size={28} color="white" />
          </TouchableOpacity>
        </View>
      </CameraView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  grantContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'transparent',
    justifyContent: 'center',
    alignItems: 'center',
  },
  guideFrame: {
    width: 280,
    height: 80,
    borderWidth: 2,
    borderColor: 'white',
    borderRadius: 10,
  },
  buttonContainer: {
    position: 'absolute',
    bottom: 40,
    alignSelf: 'center',
  },
  captureButton: {
    width: 70,
    height: 70,
    borderRadius: 35,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  flipButton: {
    position: 'absolute',
    bottom: 40,
    right: 30,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  previewContainer: {
    flex: 1,
    justifyContent: 'space-between',
  },
  preview: {
    width: '100%',
    height: '70%',
  },
  confirmationButtons: {
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 25,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  buttonText: {
    color: 'white',
    marginLeft: 8,
    fontSize: 16,
  },
  odometerInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    padding: 15,
    borderRadius: 10,
    fontSize: 16,
    marginHorizontal: 20,
    color: 'white',
    marginVertical: 20,
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  galleryButton: {
    position: 'absolute',
    bottom: 40,
    left: 30,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
}); 