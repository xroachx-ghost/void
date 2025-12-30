"""
FRP Wizard tests.

Copyright (c) 2024 Roach Labs. All rights reserved.
Made by James Michael Roach Jr.
Proprietary and confidential. Unauthorized use or distribution is prohibited.
"""

from void.core.frp import FRPEngine


def test_frp_engine_initialization():
    """Test that FRP engine initializes correctly."""
    engine = FRPEngine()
    assert engine is not None
    assert hasattr(engine, 'methods')
    assert len(engine.methods) > 0


def test_frp_detect_best_methods():
    """Test FRP method detection with sample device info."""
    engine = FRPEngine()
    
    # Sample device info
    device_info = {
        'manufacturer': 'Samsung',
        'model': 'Galaxy S21',
        'android_version': '12',
        'security_patch': '2023-05-01',
        'chipset': 'Qualcomm',
        'mode': 'adb',
        'bootloader_locked': True,
        'usb_debugging': True
    }
    
    recommendations = engine.detect_best_methods(device_info)
    
    # Check that recommendations have required keys
    assert 'primary_methods' in recommendations
    assert 'alternative_methods' in recommendations
    assert 'success_probability' in recommendations
    assert 'requirements' in recommendations
    assert 'step_by_step_guide' in recommendations
    
    # Check that some methods were recommended
    assert len(recommendations['primary_methods']) > 0
    assert len(recommendations['step_by_step_guide']) > 0


def test_frp_execute_method_unknown():
    """Test executing an unknown method returns failure."""
    engine = FRPEngine()
    result = engine.execute_method('unknown_method', 'device123')
    
    assert result is not None
    assert 'success' in result
    assert result['success'] is False
    assert 'message' in result


def test_frp_method_categories():
    """Test that methods are organized in categories."""
    engine = FRPEngine()
    
    # Check for different method prefixes
    adb_methods = [m for m in engine.methods.keys() if m.startswith('adb_')]
    fastboot_methods = [m for m in engine.methods.keys() if m.startswith('fastboot_')]
    edl_methods = [m for m in engine.methods.keys() if m.startswith('edl_')]
    recovery_methods = [m for m in engine.methods.keys() if m.startswith('recovery_')]
    
    # Check that we have methods in each category
    assert len(adb_methods) > 0
    assert len(fastboot_methods) > 0
    assert len(edl_methods) > 0
    assert len(recovery_methods) > 0


def test_frp_success_probability_calculation():
    """Test that success probabilities are calculated."""
    engine = FRPEngine()
    
    device_info = {
        'manufacturer': 'Google',
        'model': 'Pixel 6',
        'android_version': '13',
        'security_patch': '2024-01-05',
        'chipset': 'Google',
        'mode': 'adb',
        'bootloader_locked': False,
        'usb_debugging': True
    }
    
    recommendations = engine.detect_best_methods(device_info)
    success_prob = recommendations['success_probability']
    
    # Check that probabilities are assigned
    assert len(success_prob) > 0
    
    # Check that probabilities are in correct format
    for method, prob in success_prob.items():
        assert isinstance(prob, str)
        # Should contain percentage or description
        assert '%' in prob or 'expertise' in prob.lower()


def test_frp_method_requirements():
    """Test that method requirements are properly defined."""
    engine = FRPEngine()
    
    device_info = {
        'manufacturer': 'Xiaomi',
        'model': 'Redmi Note 10',
        'android_version': '11',
        'security_patch': '2023-01-01',
        'chipset': 'Qualcomm',
        'mode': 'fastboot',
        'bootloader_locked': True,
        'usb_debugging': False
    }
    
    recommendations = engine.detect_best_methods(device_info)
    requirements = recommendations['requirements']
    
    # Check that requirements are defined
    assert len(requirements) > 0
    
    # Check that each requirement has required fields
    for method, req in requirements.items():
        assert 'skill_level' in req
        assert 'tools_needed' in req
        assert 'prerequisites' in req
        assert 'risks' in req


def test_frp_step_by_step_guide():
    """Test that step-by-step guide is generated."""
    engine = FRPEngine()
    
    device_info = {
        'manufacturer': 'Samsung',
        'model': 'Galaxy A52',
        'android_version': '11',
        'security_patch': '2022-12-01',
        'chipset': 'Qualcomm',
        'mode': 'adb',
        'bootloader_locked': True,
        'usb_debugging': True
    }
    
    recommendations = engine.detect_best_methods(device_info)
    guide = recommendations['step_by_step_guide']
    
    # Check that guide has steps
    assert len(guide) > 0
    
    # Check that each step has required fields
    for step in guide:
        assert 'step' in step
        assert 'title' in step
        assert 'description' in step
        assert 'action' in step
        assert 'importance' in step


def test_frp_warnings_generation():
    """Test that appropriate warnings are generated."""
    engine = FRPEngine()
    
    # Modern device with recent patch
    device_info = {
        'manufacturer': 'Samsung',
        'model': 'Galaxy S23',
        'android_version': '14',
        'security_patch': '2024-06-01',
        'chipset': 'Qualcomm',
        'mode': 'unknown',
        'bootloader_locked': True,
        'usb_debugging': False
    }
    
    recommendations = engine.detect_best_methods(device_info)
    warnings = recommendations['warnings']
    
    # Should have warnings for recent patch and limited access
    assert len(warnings) > 0
    assert any('patch' in w.lower() or 'android 13+' in w.lower() for w in warnings)


def test_frp_wizard_status_integration():
    """Test that setup wizard status is properly integrated."""
    engine = FRPEngine()
    
    # Test with wizard loop suspected
    device_info = {
        'manufacturer': 'Samsung',
        'model': 'Galaxy S21',
        'android_version': '12',
        'security_patch': '2023-05-01',
        'chipset': 'Qualcomm',
        'mode': 'adb',
        'bootloader_locked': True,
        'usb_debugging': True,
        'wizard_status': 'wizard loop suspected',
        'wizard_running': True,
        'user_setup_complete': True
    }
    
    recommendations = engine.detect_best_methods(device_info)
    
    # Check that wizard loop warning is present
    wizard_warnings = [w for w in recommendations['warnings'] if 'WIZARD LOOP' in w]
    assert len(wizard_warnings) > 0
    assert 'FRP' in wizard_warnings[0]
    
    # Check that adb_setup_complete is prioritized
    assert 'adb_setup_complete' in recommendations['primary_methods'][:3]


def test_frp_wizard_status_setup_incomplete():
    """Test detection of setup incomplete status."""
    engine = FRPEngine()
    
    device_info = {
        'manufacturer': 'Xiaomi',
        'model': 'Redmi Note 10',
        'android_version': '11',
        'security_patch': '2022-12-01',
        'chipset': 'Qualcomm',
        'mode': 'fastboot',
        'bootloader_locked': False,
        'usb_debugging': False,
        'wizard_status': 'setup incomplete',
        'wizard_running': False,
        'user_setup_complete': False
    }
    
    recommendations = engine.detect_best_methods(device_info)
    
    # Check for setup incomplete warning
    setup_warnings = [w for w in recommendations['warnings'] if 'setup incomplete' in w.lower()]
    assert len(setup_warnings) > 0


def test_frp_wizard_backward_compatibility():
    """Test that FRP engine works without wizard status (backward compatibility)."""
    engine = FRPEngine()
    
    # Device info without wizard status fields
    device_info = {
        'manufacturer': 'OnePlus',
        'model': 'OnePlus 9',
        'android_version': '12',
        'security_patch': '2023-03-01',
        'chipset': 'Qualcomm',
        'mode': 'adb',
        'bootloader_locked': True,
        'usb_debugging': True
    }
    
    # Should work without errors
    recommendations = engine.detect_best_methods(device_info)
    
    assert 'primary_methods' in recommendations
    assert len(recommendations['primary_methods']) > 0
    assert 'warnings' in recommendations
