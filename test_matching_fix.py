<<<<<<< HEAD
#!/usr/bin/env python3
"""
Test script to verify registered faces can be matched successfully.
"""

import requests
import base64
import json
from pathlib import Path
import sys

# Backend URL
API_URL = "http://localhost:8000"

def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def register_face(image_path: str, person_name: str = "Test Person"):
    """Register a face with the backend."""
    print(f"\n[TEST] Registering face from: {image_path}")
    
    image_b64 = encode_image_to_base64(image_path)
    
    payload = {
        "person_name": person_name,
        "image_base64": image_b64,
        "additional_info": {"test": True}
    }
    
    try:
        response = requests.post(f"{API_URL}/api/register", json=payload)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            person_id = data.get('person_id')
            print(f"✓ Registration SUCCESS - Person ID: {person_id}")
            return person_id
        else:
            print(f"✗ Registration FAILED: {data}")
            return None
    except Exception as e:
        print(f"✗ Registration ERROR: {e}")
        return None

def match_face(image_path: str):
    """Match a face against registered database."""
    print(f"\n[TEST] Matching face from: {image_path}")
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post(f"{API_URL}/api/match", files=files)
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                matches = data.get('matches', [])
                print(f"✓ Matching SUCCESS - Found {len(matches)} face(s)")
                
                for face_idx, face_data in enumerate(matches):
                    face_matches = face_data.get('matches', [])
                    print(f"\n  Face #{face_idx + 1}:")
                    print(f"    Detected {len(face_matches)} candidate(s)")
                    
                    for match_idx, match in enumerate(face_matches):
                        confidence = match.get('similarity', 0)
                        status = "✓ ABOVE 0.55" if confidence >= 0.55 else "✗ BELOW 0.55"
                        print(f"    [{match_idx + 1}] {match.get('name', 'Unknown')}: {confidence:.3f} {status}")
                        if match_idx == 0:
                            return confidence >= 0.55, confidence
                
                return False, 0.0
            else:
                print(f"✗ Matching FAILED: {data}")
                return False, 0.0
        except Exception as e:
            print(f"✗ Matching ERROR: {e}")
            return False, 0.0

def get_all_persons():
    """Get all registered persons."""
    try:
        response = requests.get(f"{API_URL}/api/persons")
        data = response.json()
        if response.status_code == 200:
            persons = data.get('persons', [])
            print(f"\n[INFO] {len(persons)} persons registered:")
            for p in persons:
                print(f"  - {p['name']} (ID: {p['id']})")
            return len(persons)
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to get persons: {e}")
        return 0

def main():
    print("="*60)
    print("FACE MATCHING THRESHOLD FIX TEST")
    print("="*60)
    
    # Find a test image  
    test_dir = Path("c:/Users/Sandhya Pal/OneDrive/Desktop/cctv-surveillance/ai-dashboard-frontend/backend/face_recognition_system")
    
    # Look for any jpg/png in the directory
    test_images = list(test_dir.parent.parent.glob("*.jpg")) + list(test_dir.parent.parent.glob("*.png"))
    
    if not test_images:
        print("\n[ERROR] No test images found in project root")
        print("       Please add a test image (JPG/PNG) to test matching")
        print("\n[INFO] Current registered persons:")
        get_all_persons()
        print("\nTo test:")
        print("1. Register a face: python test_matching_fix.py register <image_path>")
        print("2. Match the same face: python test_matching_fix.py match <image_path>")
        return
    
    test_image = str(test_images[0])
    print(f"\nUsing test image: {test_image}")
    
    # Test workflow
    print("\n" + "="*60)
    print("STEP 1: Register a test face")
    print("="*60)
    person_id = register_face(test_image, "Test Person A")
    
    print("\n" + "="*60)
    print("STEP 2: Match the same face (should find it)")
    print("="*60)
    success, confidence = match_face(test_image)
    
    print("\n" + "="*60)
    print("STEP 3: List all registered persons")
    print("="*60)
    get_all_persons()
    
    print("\n" + "="*60)
    print("TEST RESULT")
    print("="*60)
    if success and person_id:
        print(f"✓ SUCCESS: Registered face was matched with confidence {confidence:.3f}")
        print("  The threshold fix is working correctly!")
    elif person_id and confidence > 0:
        print(f"⚠ PARTIAL: Face was registered (ID: {person_id})")
        print(f"  but matching returned {confidence:.3f} (below 0.55 threshold)")
        print("  This suggests the faces may need better lighting or angle")
    else:
        print("✗ FAILURE: Something went wrong during testing")

if __name__ == "__main__":
    main()
=======
#!/usr/bin/env python3
"""
Test script to verify registered faces can be matched successfully.
"""

import requests
import base64
import json
from pathlib import Path
import sys

# Backend URL
API_URL = "http://localhost:8000"

def encode_image_to_base64(image_path: str) -> str:
    """Encode image file to base64."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def register_face(image_path: str, person_name: str = "Test Person"):
    """Register a face with the backend."""
    print(f"\n[TEST] Registering face from: {image_path}")
    
    image_b64 = encode_image_to_base64(image_path)
    
    payload = {
        "person_name": person_name,
        "image_base64": image_b64,
        "additional_info": {"test": True}
    }
    
    try:
        response = requests.post(f"{API_URL}/api/register", json=payload)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            person_id = data.get('person_id')
            print(f"✓ Registration SUCCESS - Person ID: {person_id}")
            return person_id
        else:
            print(f"✗ Registration FAILED: {data}")
            return None
    except Exception as e:
        print(f"✗ Registration ERROR: {e}")
        return None

def match_face(image_path: str):
    """Match a face against registered database."""
    print(f"\n[TEST] Matching face from: {image_path}")
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        try:
            response = requests.post(f"{API_URL}/api/match", files=files)
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                matches = data.get('matches', [])
                print(f"✓ Matching SUCCESS - Found {len(matches)} face(s)")
                
                for face_idx, face_data in enumerate(matches):
                    face_matches = face_data.get('matches', [])
                    print(f"\n  Face #{face_idx + 1}:")
                    print(f"    Detected {len(face_matches)} candidate(s)")
                    
                    for match_idx, match in enumerate(face_matches):
                        confidence = match.get('similarity', 0)
                        status = "✓ ABOVE 0.55" if confidence >= 0.55 else "✗ BELOW 0.55"
                        print(f"    [{match_idx + 1}] {match.get('name', 'Unknown')}: {confidence:.3f} {status}")
                        if match_idx == 0:
                            return confidence >= 0.55, confidence
                
                return False, 0.0
            else:
                print(f"✗ Matching FAILED: {data}")
                return False, 0.0
        except Exception as e:
            print(f"✗ Matching ERROR: {e}")
            return False, 0.0

def get_all_persons():
    """Get all registered persons."""
    try:
        response = requests.get(f"{API_URL}/api/persons")
        data = response.json()
        if response.status_code == 200:
            persons = data.get('persons', [])
            print(f"\n[INFO] {len(persons)} persons registered:")
            for p in persons:
                print(f"  - {p['name']} (ID: {p['id']})")
            return len(persons)
        return 0
    except Exception as e:
        print(f"[ERROR] Failed to get persons: {e}")
        return 0

def main():
    print("="*60)
    print("FACE MATCHING THRESHOLD FIX TEST")
    print("="*60)
    
    # Find a test image  
    test_dir = Path("c:/Users/Sandhya Pal/OneDrive/Desktop/cctv-surveillance/ai-dashboard-frontend/backend/face_recognition_system")
    
    # Look for any jpg/png in the directory
    test_images = list(test_dir.parent.parent.glob("*.jpg")) + list(test_dir.parent.parent.glob("*.png"))
    
    if not test_images:
        print("\n[ERROR] No test images found in project root")
        print("       Please add a test image (JPG/PNG) to test matching")
        print("\n[INFO] Current registered persons:")
        get_all_persons()
        print("\nTo test:")
        print("1. Register a face: python test_matching_fix.py register <image_path>")
        print("2. Match the same face: python test_matching_fix.py match <image_path>")
        return
    
    test_image = str(test_images[0])
    print(f"\nUsing test image: {test_image}")
    
    # Test workflow
    print("\n" + "="*60)
    print("STEP 1: Register a test face")
    print("="*60)
    person_id = register_face(test_image, "Test Person A")
    
    print("\n" + "="*60)
    print("STEP 2: Match the same face (should find it)")
    print("="*60)
    success, confidence = match_face(test_image)
    
    print("\n" + "="*60)
    print("STEP 3: List all registered persons")
    print("="*60)
    get_all_persons()
    
    print("\n" + "="*60)
    print("TEST RESULT")
    print("="*60)
    if success and person_id:
        print(f"✓ SUCCESS: Registered face was matched with confidence {confidence:.3f}")
        print("  The threshold fix is working correctly!")
    elif person_id and confidence > 0:
        print(f"⚠ PARTIAL: Face was registered (ID: {person_id})")
        print(f"  but matching returned {confidence:.3f} (below 0.55 threshold)")
        print("  This suggests the faces may need better lighting or angle")
    else:
        print("✗ FAILURE: Something went wrong during testing")

if __name__ == "__main__":
    main()
>>>>>>> f9997946d8390939c3acaf22ce5a03c8729da55e
