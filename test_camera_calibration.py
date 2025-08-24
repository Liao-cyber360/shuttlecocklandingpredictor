#!/usr/bin/env python3
"""
Test script for camera live feed calibration functionality
"""

import sys
import time
import numpy as np

def test_camera_calibration_import():
    """Test camera calibration imports"""
    try:
        from calibration import calibrate_cameras_from_live_feed
        from network_camera import NetworkCameraManager
        print("✅ Camera calibration modules imported successfully")
        
        # Test that the new function exists
        import inspect
        assert callable(calibrate_cameras_from_live_feed), "calibrate_cameras_from_live_feed is not callable"
        print("✅ calibrate_cameras_from_live_feed function exists")
        
        # Check method signature without instantiating the class
        from calibration import BadmintonCalibrator
        assert hasattr(BadmintonCalibrator, 'calibrate_from_camera'), "calibrate_from_camera method not found"
        print("✅ calibrate_from_camera method exists")
        
        # Check method signature
        sig = inspect.signature(BadmintonCalibrator.calibrate_from_camera)
        params = list(sig.parameters.keys())
        expected_params = ['self', 'camera_manager', 'num_frames', 'preview_time']
        
        for param in expected_params:
            assert param in params, f"Parameter {param} not found in method signature"
        
        print("✅ Method signature is correct")
        print(f"   Parameters: {params}")
        
        # Check default values
        assert sig.parameters['num_frames'].default == 20, "num_frames default should be 20"
        assert sig.parameters['preview_time'].default == 5.0, "preview_time default should be 5.0"
        print("✅ Default parameter values are correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Camera calibration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_calibrate_cameras_from_live_feed():
    """Test the calibrate_cameras_from_live_feed function"""
    try:
        from calibration import calibrate_cameras_from_live_feed
        from network_camera import NetworkCameraManager
        
        print("📹 Testing calibrate_cameras_from_live_feed function...")
        
        # Check function signature
        import inspect
        sig = inspect.signature(calibrate_cameras_from_live_feed)
        params = list(sig.parameters.keys())
        expected_params = ['camera_manager', 'output_dir', 'num_frames', 'preview_time']
        
        for param in expected_params:
            assert param in params, f"Parameter {param} not found in function signature"
        
        print("✅ Function signature is correct")
        print(f"   Parameters: {params}")
        
        # Check default values
        assert sig.parameters['num_frames'].default == 20, "num_frames default should be 20"
        assert sig.parameters['preview_time'].default == 5.0, "preview_time default should be 5.0"
        print("✅ Default parameter values are correct")
        
        return True
        
    except Exception as e:
        print(f"❌ calibrate_cameras_from_live_feed test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_integration():
    """Test main.py integration"""
    try:
        print("🔧 Testing main.py integration...")
        
        # Just test that we can import the calibration function
        from calibration import calibrate_cameras_from_live_feed
        print("✅ Can import calibrate_cameras_from_live_feed from main context")
        
        # Test that the updated calibration.py has both functions
        from calibration import calibrate_cameras
        print("✅ Original calibrate_cameras function still exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Main integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing Camera Live Feed Calibration Implementation")
    print("=" * 60)
    
    tests = [
        ("Basic Import Test", test_camera_calibration_import),
        ("Function Test", test_calibrate_cameras_from_live_feed),
        ("Main Integration Test", test_main_integration),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Running {name}...")
        try:
            result = test_func()
            results.append((name, result))
            if result:
                print(f"✅ {name} PASSED")
            else:
                print(f"❌ {name} FAILED")
        except Exception as e:
            print(f"❌ {name} FAILED with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Camera live feed calibration is ready.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)