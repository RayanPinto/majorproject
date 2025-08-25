#!/usr/bin/env python3
"""
Simple system test to verify the agent system is working correctly
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("🧪 Testing imports...")
    
    try:
        from manager.agent import state_manager_agent
        print("✅ Main agent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import main agent: {e}")
        return False
    
    try:
        from manager.sub_agents.state_agent import state_agent
        print("✅ State agent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import state agent: {e}")
        return False
    
    try:
        from manager.sub_agents.conversational_agent import conversational_agent
        print("✅ Conversational agent imported successfully")
    except Exception as e:
        print(f"❌ Failed to import conversational agent: {e}")
        return False
    
    try:
        from main import (
            StateManagementError, ValidationError, JSONProcessingError,
            StateUpdateError, DatabaseError, UserInputError,
            validate_json_structure, validate_user_input, format_error_response
        )
        print("✅ Error handling classes imported successfully")
    except Exception as e:
        print(f"❌ Failed to import error handling classes: {e}")
        return False
    
    return True

def test_agent_initialization():
    """Test that agents can be initialized"""
    print("\n🧪 Testing agent initialization...")
    
    try:
        from manager.agent import state_manager_agent
        from manager.sub_agents.state_agent import state_agent
        from manager.sub_agents.conversational_agent import conversational_agent
        
        # Check that agents have required attributes
        assert hasattr(state_manager_agent, 'name'), "Main agent missing name"
        assert hasattr(state_agent, 'name'), "State agent missing name"
        assert hasattr(conversational_agent, 'name'), "Conversational agent missing name"
        
        print("✅ All agents initialized successfully")
        print(f"   Main agent: {state_manager_agent.name}")
        print(f"   State agent: {state_agent.name}")
        print(f"   Conversational agent: {conversational_agent.name}")
        
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

def test_error_handling():
    """Test basic error handling functionality"""
    print("\n🧪 Testing error handling...")
    
    try:
        from main import (
            StateManagementError, ValidationError, JSONProcessingError,
            validate_json_structure, validate_user_input, format_error_response
        )
        
        # Test error creation
        error = ValidationError("Test error", "TEST_001")
        assert error.message == "Test error", "Error message not set correctly"
        assert error.error_code == "TEST_001", "Error code not set correctly"
        
        # Test JSON validation
        result = validate_json_structure({"_id": "123"}, ["_id", "user_id"])
        assert result["valid"] == True, "Valid JSON should be valid"
        assert len(result["warnings"]) > 0, "Should have warnings for missing keys"
        
        # Test error formatting
        formatted = format_error_response(error)
        assert "Validation Error:" in formatted, "Error formatting not working"
        
        print("✅ Error handling working correctly")
        return True
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_utils():
    """Test utility functions"""
    print("\n🧪 Testing utility functions...")
    
    try:
        from utils import Colors, log_json_input, display_state
        
        # Test color codes
        assert hasattr(Colors, 'GREEN'), "Colors class missing GREEN"
        assert hasattr(Colors, 'RED'), "Colors class missing RED"
        
        print("✅ Utility functions available")
        return True
    except Exception as e:
        print(f"❌ Utility functions test failed: {e}")
        return False

def main():
    """Run all system tests"""
    print("🚀 Starting System Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_agent_initialization,
        test_error_handling,
        test_utils
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print("📊 SYSTEM TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"🎯 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All system tests passed! The system is ready to use.")
        return 0
    else:
        print("\n⚠️ Some system tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
