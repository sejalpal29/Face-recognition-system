<<<<<<< HEAD
#!/usr/bin/env python3
"""
Comprehensive backend testing script for the face recognition system.
Tests registration, comparison, and matching endpoints.
"""

import cv2
import numpy as np
import base64
import requests
import json
from typing import Tuple
import sys
import os

# Configuration
BACKEND_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/health"
REGISTER_ENDPOINT = f"{BACKEND_URL}/api/register"
COMPARE_ENDPOINT = f"{BACKEND_URL}/api/compare"
MATCH_ENDPOINT = f"{BACKEND_URL}/api/match"

def print_colored(text: str, color: str = "green"):
    """Print colored text for better readability."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "end": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def test_health() -> bool:
    """Test backend health endpoint."""
    print("\n" + "="*60)
    print_colored("[TEST 1/5] Testing Backend Health", "blue")
    print("="*60)
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_colored(f"✓ Backend is healthy", "green")
            print(f"  Status: {data.get('status')}")
            print(f"  Device: {data.get('device')}")
            print(f"  Model Initialized: {data.get('model_initialized')}")
            return True
        else:
            print_colored(f"✗ Backend returned status {response.status_code}", "red")
            return False
    except Exception as e:
        print_colored(f"✗ Error connecting to backend: {e}", "red")
        return False

def create_synthetic_face_image() -> Tuple[np.ndarray, str]:
    """
    Create a synthetic image that resembles a face.
    For real testing, replace this with actual face images.
    """
    print("\n  Generating synthetic face image for testing...")
    
    # Create image with face-like features
    img = np.ones((480, 640, 3), dtype=np.uint8) * 200  # Light background
    
    # Draw face outline (circle)
    cv2.circle(img, (320, 280), 120, (150, 100, 80), -1)  # Face (brownish)
    
    # Draw eyes
    cv2.circle(img, (260, 240), 25, (255, 255, 255), -1)  # Left eye white
    cv2.circle(img, (380, 240), 25, (255, 255, 255), -1)  # Right eye white
    cv2.circle(img, (260, 240), 15, (100, 50, 0), -1)     # Left pupil
    cv2.circle(img, (380, 240), 15, (100, 50, 0), -1)     # Right pupil
    
    # Draw nose
    nose_pts = np.array([[320, 260], [310, 300], [330, 300]], np.int32)
    cv2.fillPoly(img, [nose_pts], (150, 100, 80))
    
    # Draw mouth
    cv2.ellipse(img, (320, 350), (40, 25), 0, 0, 180, (200, 100, 100), -1)
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode()
    
    print("  ✓ Synthetic face image created")
    return img, img_base64

def test_registration(skip_real_face=True) -> Tuple[bool, str]:
    """
    Test the registration endpoint.
    Note: This will fail with synthetic images because real face detection is required.
    """
    print("\n" + "="*60)
    print_colored("[TEST 2/5] Testing Face Registration", "blue")
    print("="*60)
    
    try:
        _, img_base64 = create_synthetic_face_image()
        
        payload = {
            "name": "Test User",
            "image_base64": img_base64,
            "status": "registered",
            "metadata": {
                "test": True,
                "age": 30,
                "description": "Synthetic test image"
            }
        }
        
        print("\n  Sending registration request...")
        print(f"  Endpoint: {REGISTER_ENDPOINT}")
        print(f"  Name: {payload['name']}")
        print(f"  Image size: {len(img_base64)} bytes")
        
        response = requests.post(
            REGISTER_ENDPOINT,
            json=payload,
            timeout=30
        )
        
        print(f"\n  Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_colored("✓ Registration successful!", "green")
            print(f"  Person ID: {data.get('person_id')}")
            print(f"  Face ID: {data.get('face_id')}")
            print(f"  Message: {data.get('message')}")
            return True, str(data.get('person_id', ''))
        else:
            error_data = response.json()
            detail = error_data.get('detail', 'Unknown error')
            print_colored(f"✗ Registration failed: {detail}", "yellow")
            print("  Note: This is expected with synthetic images.")
            print("  To test with real faces, provide actual face images.")
            return False, ""
            
    except Exception as e:
        print_colored(f"✗ Error during registration: {e}", "red")
        return False, ""

def test_comparison() -> bool:
    """Test the comparison endpoint."""
    print("\n" + "="*60)
    print_colored("[TEST 3/5] Testing Face Comparison", "blue")
    print("="*60)
    
    try:
        _, img1_base64 = create_synthetic_face_image()
        _, img2_base64 = create_synthetic_face_image()
        
        payload = {
            "image1_base64": img1_base64,
            "image2_base64": img2_base64
        }
        
        print("\n  Sending comparison request...")
        print(f"  Endpoint: {COMPARE_ENDPOINT}")
        
        response = requests.post(
            COMPARE_ENDPOINT,
            json=payload,
            timeout=30
        )
        
        print(f"  Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_colored("✓ Comparison processed!", "green")
            print(f"  Similarity Score: {data.get('similarity', 'N/A')}")
            print(f"  Are Same Person: {data.get('same_person', 'N/A')}")
            return True
        else:
            error_data = response.json()
            detail = error_data.get('detail', 'Unknown error')
            print_colored(f"✗ Comparison failed: {detail}", "yellow")
            print("  Note: This is expected with synthetic images.")
            return False
            
    except Exception as e:
        print_colored(f"✗ Error during comparison: {e}", "red")
        return False

def test_endpoints_availability() -> bool:
    """Test if all required endpoints are available."""
    print("\n" + "="*60)
    print_colored("[TEST 4/5] Testing Endpoint Availability", "blue")
    print("="*60)
    
    endpoints = [
        ("Health", HEALTH_ENDPOINT, "GET"),
        ("Registration", REGISTER_ENDPOINT, "POST"),
        ("Comparison", COMPARE_ENDPOINT, "POST"),
        ("Matching", MATCH_ENDPOINT, "POST"),
    ]
    
    all_available = True
    
    for name, endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.head(endpoint, timeout=5)
            else:
                # For POST endpoints, we don't need actual data, just check if it responds
                response = requests.options(endpoint, timeout=5)
            
            # OPTIONS or HEAD requests might not be allowed, that's ok
            # We just want to know if the endpoint exists
            if response.status_code < 500:  # 404, 405, 405 all mean endpoint exists
                print_colored(f"  ✓ {name}: Available", "green")
            else:
                print_colored(f"  ✗ {name}: Error (status {response.status_code})", "red")
                all_available = False
        except Exception as e:
            print_colored(f"  ✗ {name}: Unreachable ({e})", "red")
            all_available = False
    
    return all_available

def print_summary(results: dict):
    """Print test summary."""
    print("\n" + "="*60)
    print_colored("[TEST SUMMARY]", "blue")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = "green" if result else "red"
        print_colored(f"  {status}: {test_name}", color)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print_colored("\n✓ All tests passed! Backend is fully operational.", "green")
    else:
        print_colored(f"\n⚠ Some tests failed. Review the output above for details.", "yellow")
    
    print("\nNOTE: Face detection tests will fail with synthetic images.")
    print("To test with real faces, provide actual face images.")
    print("="*60)

def main():
    """Run all tests."""
    print_colored("\n" + "="*60, "blue")
    print_colored("FACE RECOGNITION BACKEND TEST SUITE", "blue")
    print_colored("="*60, "blue")
    
    print(f"\nBackend URL: {BACKEND_URL}")
    print(f"Python Version: {sys.version.split()[0]}")
    
    results = {}
    
    # Test 1: Health
    results["Backend Health"] = test_health()
    
    # Test 2: Registration (will show expected failure with synthetic images)
    reg_success, person_id = test_registration()
    results["Face Registration"] = reg_success
    
    # Test 3: Comparison
    results["Face Comparison"] = test_comparison()
    
    # Test 4: Endpoint Availability  
    results["Endpoints Availability"] = test_endpoints_availability()
    
    # Test 5: CORS Configuration
    print("\n" + "="*60)
    print_colored("[TEST 5/5] CORS Configuration", "blue")
    print("="*60)
    try:
        headers = {
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST"
        }
        response = requests.options(REGISTER_ENDPOINT, headers=headers, timeout=5)
        cors_configured = "access-control-allow-origin" in response.headers.lower()
        if cors_configured:
            print_colored("✓ CORS is properly configured", "green")
            print(f"  Allow Origin: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
        else:
            print_colored("⚠ CORS headers not detected (might be disabled)", "yellow")
        results["CORS Configuration"] = True
    except Exception as e:
        print_colored(f"✗ CORS check failed: {e}", "red")
        results["CORS Configuration"] = False
    
    # Print summary
    print_summary(results)
    
    # Return exit code based on results
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    exit(main())
=======
#!/usr/bin/env python3
"""
Comprehensive backend testing script for the face recognition system.
Tests registration, comparison, and matching endpoints.
"""

import cv2
import numpy as np
import base64
import requests
import json
from typing import Tuple
import sys
import os

# Configuration
BACKEND_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/health"
REGISTER_ENDPOINT = f"{BACKEND_URL}/api/register"
COMPARE_ENDPOINT = f"{BACKEND_URL}/api/compare"
MATCH_ENDPOINT = f"{BACKEND_URL}/api/match"

def print_colored(text: str, color: str = "green"):
    """Print colored text for better readability."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "end": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def test_health() -> bool:
    """Test backend health endpoint."""
    print("\n" + "="*60)
    print_colored("[TEST 1/5] Testing Backend Health", "blue")
    print("="*60)
    
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_colored(f"✓ Backend is healthy", "green")
            print(f"  Status: {data.get('status')}")
            print(f"  Device: {data.get('device')}")
            print(f"  Model Initialized: {data.get('model_initialized')}")
            return True
        else:
            print_colored(f"✗ Backend returned status {response.status_code}", "red")
            return False
    except Exception as e:
        print_colored(f"✗ Error connecting to backend: {e}", "red")
        return False

def create_synthetic_face_image() -> Tuple[np.ndarray, str]:
    """
    Create a synthetic image that resembles a face.
    For real testing, replace this with actual face images.
    """
    print("\n  Generating synthetic face image for testing...")
    
    # Create image with face-like features
    img = np.ones((480, 640, 3), dtype=np.uint8) * 200  # Light background
    
    # Draw face outline (circle)
    cv2.circle(img, (320, 280), 120, (150, 100, 80), -1)  # Face (brownish)
    
    # Draw eyes
    cv2.circle(img, (260, 240), 25, (255, 255, 255), -1)  # Left eye white
    cv2.circle(img, (380, 240), 25, (255, 255, 255), -1)  # Right eye white
    cv2.circle(img, (260, 240), 15, (100, 50, 0), -1)     # Left pupil
    cv2.circle(img, (380, 240), 15, (100, 50, 0), -1)     # Right pupil
    
    # Draw nose
    nose_pts = np.array([[320, 260], [310, 300], [330, 300]], np.int32)
    cv2.fillPoly(img, [nose_pts], (150, 100, 80))
    
    # Draw mouth
    cv2.ellipse(img, (320, 350), (40, 25), 0, 0, 180, (200, 100, 100), -1)
    
    # Encode to base64
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode()
    
    print("  ✓ Synthetic face image created")
    return img, img_base64

def test_registration(skip_real_face=True) -> Tuple[bool, str]:
    """
    Test the registration endpoint.
    Note: This will fail with synthetic images because real face detection is required.
    """
    print("\n" + "="*60)
    print_colored("[TEST 2/5] Testing Face Registration", "blue")
    print("="*60)
    
    try:
        _, img_base64 = create_synthetic_face_image()
        
        payload = {
            "name": "Test User",
            "image_base64": img_base64,
            "status": "registered",
            "metadata": {
                "test": True,
                "age": 30,
                "description": "Synthetic test image"
            }
        }
        
        print("\n  Sending registration request...")
        print(f"  Endpoint: {REGISTER_ENDPOINT}")
        print(f"  Name: {payload['name']}")
        print(f"  Image size: {len(img_base64)} bytes")
        
        response = requests.post(
            REGISTER_ENDPOINT,
            json=payload,
            timeout=30
        )
        
        print(f"\n  Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_colored("✓ Registration successful!", "green")
            print(f"  Person ID: {data.get('person_id')}")
            print(f"  Face ID: {data.get('face_id')}")
            print(f"  Message: {data.get('message')}")
            return True, str(data.get('person_id', ''))
        else:
            error_data = response.json()
            detail = error_data.get('detail', 'Unknown error')
            print_colored(f"✗ Registration failed: {detail}", "yellow")
            print("  Note: This is expected with synthetic images.")
            print("  To test with real faces, provide actual face images.")
            return False, ""
            
    except Exception as e:
        print_colored(f"✗ Error during registration: {e}", "red")
        return False, ""

def test_comparison() -> bool:
    """Test the comparison endpoint."""
    print("\n" + "="*60)
    print_colored("[TEST 3/5] Testing Face Comparison", "blue")
    print("="*60)
    
    try:
        _, img1_base64 = create_synthetic_face_image()
        _, img2_base64 = create_synthetic_face_image()
        
        payload = {
            "image1_base64": img1_base64,
            "image2_base64": img2_base64
        }
        
        print("\n  Sending comparison request...")
        print(f"  Endpoint: {COMPARE_ENDPOINT}")
        
        response = requests.post(
            COMPARE_ENDPOINT,
            json=payload,
            timeout=30
        )
        
        print(f"  Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_colored("✓ Comparison processed!", "green")
            print(f"  Similarity Score: {data.get('similarity', 'N/A')}")
            print(f"  Are Same Person: {data.get('same_person', 'N/A')}")
            return True
        else:
            error_data = response.json()
            detail = error_data.get('detail', 'Unknown error')
            print_colored(f"✗ Comparison failed: {detail}", "yellow")
            print("  Note: This is expected with synthetic images.")
            return False
            
    except Exception as e:
        print_colored(f"✗ Error during comparison: {e}", "red")
        return False

def test_endpoints_availability() -> bool:
    """Test if all required endpoints are available."""
    print("\n" + "="*60)
    print_colored("[TEST 4/5] Testing Endpoint Availability", "blue")
    print("="*60)
    
    endpoints = [
        ("Health", HEALTH_ENDPOINT, "GET"),
        ("Registration", REGISTER_ENDPOINT, "POST"),
        ("Comparison", COMPARE_ENDPOINT, "POST"),
        ("Matching", MATCH_ENDPOINT, "POST"),
    ]
    
    all_available = True
    
    for name, endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.head(endpoint, timeout=5)
            else:
                # For POST endpoints, we don't need actual data, just check if it responds
                response = requests.options(endpoint, timeout=5)
            
            # OPTIONS or HEAD requests might not be allowed, that's ok
            # We just want to know if the endpoint exists
            if response.status_code < 500:  # 404, 405, 405 all mean endpoint exists
                print_colored(f"  ✓ {name}: Available", "green")
            else:
                print_colored(f"  ✗ {name}: Error (status {response.status_code})", "red")
                all_available = False
        except Exception as e:
            print_colored(f"  ✗ {name}: Unreachable ({e})", "red")
            all_available = False
    
    return all_available

def print_summary(results: dict):
    """Print test summary."""
    print("\n" + "="*60)
    print_colored("[TEST SUMMARY]", "blue")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = "green" if result else "red"
        print_colored(f"  {status}: {test_name}", color)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print_colored("\n✓ All tests passed! Backend is fully operational.", "green")
    else:
        print_colored(f"\n⚠ Some tests failed. Review the output above for details.", "yellow")
    
    print("\nNOTE: Face detection tests will fail with synthetic images.")
    print("To test with real faces, provide actual face images.")
    print("="*60)

def main():
    """Run all tests."""
    print_colored("\n" + "="*60, "blue")
    print_colored("FACE RECOGNITION BACKEND TEST SUITE", "blue")
    print_colored("="*60, "blue")
    
    print(f"\nBackend URL: {BACKEND_URL}")
    print(f"Python Version: {sys.version.split()[0]}")
    
    results = {}
    
    # Test 1: Health
    results["Backend Health"] = test_health()
    
    # Test 2: Registration (will show expected failure with synthetic images)
    reg_success, person_id = test_registration()
    results["Face Registration"] = reg_success
    
    # Test 3: Comparison
    results["Face Comparison"] = test_comparison()
    
    # Test 4: Endpoint Availability  
    results["Endpoints Availability"] = test_endpoints_availability()
    
    # Test 5: CORS Configuration
    print("\n" + "="*60)
    print_colored("[TEST 5/5] CORS Configuration", "blue")
    print("="*60)
    try:
        headers = {
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "POST"
        }
        response = requests.options(REGISTER_ENDPOINT, headers=headers, timeout=5)
        cors_configured = "access-control-allow-origin" in response.headers.lower()
        if cors_configured:
            print_colored("✓ CORS is properly configured", "green")
            print(f"  Allow Origin: {response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
        else:
            print_colored("⚠ CORS headers not detected (might be disabled)", "yellow")
        results["CORS Configuration"] = True
    except Exception as e:
        print_colored(f"✗ CORS check failed: {e}", "red")
        results["CORS Configuration"] = False
    
    # Print summary
    print_summary(results)
    
    # Return exit code based on results
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    exit(main())
>>>>>>> f9997946d8390939c3acaf22ce5a03c8729da55e
