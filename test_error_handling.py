#!/usr/bin/env python3
"""
Comprehensive Error Handling Test Suite for State Management System
Tests various error scenarios and validates error handling mechanisms
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import (
    StateManagementError, ValidationError, JSONProcessingError, 
    StateUpdateError, DatabaseError, UserInputError,
    validate_json_structure, validate_user_input, format_error_response
)

class ErrorHandlingTester:
    """Test suite for error handling scenarios"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        print()
        
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def test_exception_classes(self):
        """Test custom exception classes"""
        print("🧪 Testing Exception Classes...")
        
        # Test base exception
        try:
            raise StateManagementError("Test base error", "TEST_001", {"test": True})
            self.log_test("Base Exception Creation", False, "Exception should have been raised")
        except StateManagementError as e:
            self.log_test("Base Exception Creation", True, f"Error code: {e.error_code}")
        
        # Test validation error
        try:
            raise ValidationError("Test validation error", "VAL_001")
            self.log_test("Validation Exception", False, "Exception should have been raised")
        except ValidationError as e:
            self.log_test("Validation Exception", True, f"Message: {e.message}")
        
        # Test JSON processing error
        try:
            raise JSONProcessingError("Test JSON error", "JSON_001", {"json": "test"})
            self.log_test("JSON Processing Exception", False, "Exception should have been raised")
        except JSONProcessingError as e:
            self.log_test("JSON Processing Exception", True, f"Details: {e.details}")
    
    def test_json_validation(self):
        """Test JSON structure validation"""
        print("🧪 Testing JSON Validation...")
        
        template_keys = ["_id", "user_id", "jwt"]
        
        # Test valid JSON
        valid_json = {"_id": "123", "user_id": "user1", "jwt": "token123"}
        result = validate_json_structure(valid_json, template_keys)
        self.log_test("Valid JSON Structure", result["valid"], f"Warnings: {result['warnings']}")
        
        # Test missing keys
        missing_keys_json = {"_id": "123", "user_id": "user1"}
        result = validate_json_structure(missing_keys_json, template_keys)
        self.log_test("Missing Keys JSON", result["valid"], f"Warnings: {result['warnings']}")
        
        # Test extra keys
        extra_keys_json = {"_id": "123", "user_id": "user1", "jwt": "token123", "extra": "value"}
        result = validate_json_structure(extra_keys_json, template_keys)
        self.log_test("Extra Keys JSON", result["valid"], f"Warnings: {result['warnings']}")
        
        # Test invalid data types
        invalid_types_json = {"_id": "123", "user_id": ["invalid"], "jwt": "token123"}
        result = validate_json_structure(invalid_types_json, template_keys)
        self.log_test("Invalid Data Types", not result["valid"], f"Errors: {result['errors']}")
        
        # Test empty JSON
        empty_json = {}
        result = validate_json_structure(empty_json, template_keys)
        self.log_test("Empty JSON", result["valid"], f"Warnings: {result['warnings']}")
    
    def test_user_input_validation(self):
        """Test user input validation"""
        print("🧪 Testing User Input Validation...")
        
        # Test valid JSON command
        valid_json_cmd = 'Process this JSON: {"_id": "123", "user_id": "user1"}'
        result = validate_user_input(valid_json_cmd)
        self.log_test("Valid JSON Command", result["valid"])
        
        # Test invalid JSON command
        invalid_json_cmd = 'Process this JSON: {"_id": "123", "user_id":}'
        result = validate_user_input(invalid_json_cmd)
        self.log_test("Invalid JSON Command", not result["valid"], f"Errors: {result['errors']}")
        
        # Test empty JSON command
        empty_json_cmd = "Process this JSON:"
        result = validate_user_input(empty_json_cmd)
        self.log_test("Empty JSON Command", not result["valid"], f"Errors: {result['errors']}")
        
        # Test valid update command
        valid_update_cmd = "Update state: _id=123"
        result = validate_user_input(valid_update_cmd)
        self.log_test("Valid Update Command", result["valid"])
        
        # Test invalid update command
        invalid_update_cmd = "Update state:"
        result = validate_user_input(invalid_update_cmd)
        self.log_test("Invalid Update Command", not result["valid"], f"Errors: {result['errors']}")
        
        # Test update command without equals
        no_equals_cmd = "Update state: _id 123"
        result = validate_user_input(no_equals_cmd)
        self.log_test("Update Command No Equals", not result["valid"], f"Errors: {result['errors']}")
        
        # Test empty command
        empty_cmd = ""
        result = validate_user_input(empty_cmd)
        self.log_test("Empty Command", not result["valid"], f"Errors: {result['errors']}")
        
        # Test whitespace command
        whitespace_cmd = "   "
        result = validate_user_input(whitespace_cmd)
        self.log_test("Whitespace Command", not result["valid"], f"Errors: {result['errors']}")
    
    def test_error_response_formatting(self):
        """Test error response formatting"""
        print("🧪 Testing Error Response Formatting...")
        
        # Test validation error formatting
        val_error = ValidationError("Test validation error", "VAL_001")
        response = format_error_response(val_error)
        self.log_test("Validation Error Formatting", "Validation Error:" in response)
        
        # Test JSON processing error formatting
        json_error = JSONProcessingError("Test JSON error", "JSON_001")
        response = format_error_response(json_error)
        self.log_test("JSON Error Formatting", "JSON Processing Error:" in response)
        
        # Test state update error formatting
        state_error = StateUpdateError("Test state error", "STATE_001")
        response = format_error_response(state_error)
        self.log_test("State Error Formatting", "State Update Error:" in response)
        
        # Test database error formatting
        db_error = DatabaseError("Test database error", "DB_001")
        response = format_error_response(db_error)
        self.log_test("Database Error Formatting", "Database Error:" in response)
        
        # Test user input error formatting
        input_error = UserInputError("Test input error", "INPUT_001")
        response = format_error_response(input_error)
        self.log_test("Input Error Formatting", "Input Error:" in response)
        
        # Test generic error formatting
        generic_error = Exception("Test generic error")
        response = format_error_response(generic_error)
        self.log_test("Generic Error Formatting", "System Error:" in response)
        
        # Test technical error formatting
        tech_error = ValidationError("Technical error", "TECH_001")
        response = format_error_response(tech_error, user_friendly=False)
        self.log_test("Technical Error Formatting", "Error:" in response)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("🧪 Testing Edge Cases...")
        
        # Test very large JSON
        large_json = {"_id": "x" * 1000, "user_id": "y" * 1000, "jwt": "z" * 1000}
        result = validate_json_structure(large_json, ["_id", "user_id", "jwt"])
        self.log_test("Large JSON Values", result["valid"])
        
        # Test special characters in JSON
        special_chars_json = {"_id": "test\n\t\r", "user_id": "test\"'\\", "jwt": "test{}[]"}
        result = validate_json_structure(special_chars_json, ["_id", "user_id", "jwt"])
        self.log_test("Special Characters JSON", result["valid"])
        
        # Test numeric values
        numeric_json = {"_id": 123, "user_id": 456, "jwt": "token"}
        result = validate_json_structure(numeric_json, ["_id", "user_id", "jwt"])
        self.log_test("Numeric Values JSON", result["valid"])
        
        # Test boolean values
        boolean_json = {"_id": True, "user_id": False, "jwt": "token"}
        result = validate_json_structure(boolean_json, ["_id", "user_id", "jwt"])
        self.log_test("Boolean Values JSON", result["valid"])
        
        # Test null values
        null_json = {"_id": None, "user_id": "user1", "jwt": None}
        result = validate_json_structure(null_json, ["_id", "user_id", "jwt"])
        self.log_test("Null Values JSON", result["valid"])
        
        # Test empty string values
        empty_strings_json = {"_id": "", "user_id": "", "jwt": ""}
        result = validate_json_structure(empty_strings_json, ["_id", "user_id", "jwt"])
        self.log_test("Empty String Values JSON", result["valid"])
    
    def test_malformed_inputs(self):
        """Test various malformed inputs"""
        print("🧪 Testing Malformed Inputs...")
        
        # Test malformed JSON strings
        malformed_inputs = [
            'Process this JSON: {"_id": "123",}',  # Trailing comma
            'Process this JSON: {"_id": "123"',    # Missing closing brace
            'Process this JSON: {_id: "123"}',     # Missing quotes
            'Process this JSON: {"_id": 123,}',    # Trailing comma with number
            'Process this JSON: {"_id": "123", "user_id":}',  # Incomplete value
        ]
        
        for i, malformed_input in enumerate(malformed_inputs):
            result = validate_user_input(malformed_input)
            self.log_test(f"Malformed JSON {i+1}", not result["valid"], f"Input: {malformed_input}")
        
        # Test malformed update commands
        malformed_updates = [
            "Update state: =value",           # Empty key
            "Update state: key=",             # Empty value
            "Update state: key value",        # No equals
            "Update state: key=value extra",  # Extra text
            "Update state:",                  # No key-value
        ]
        
        for i, malformed_update in enumerate(malformed_updates):
            result = validate_user_input(malformed_update)
            self.log_test(f"Malformed Update {i+1}", not result["valid"], f"Input: {malformed_update}")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Error Handling Test Suite")
        print("=" * 60)
        
        self.test_exception_classes()
        self.test_json_validation()
        self.test_user_input_validation()
        self.test_error_response_formatting()
        self.test_edge_cases()
        self.test_malformed_inputs()
        
        # Print summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Total: {self.passed_tests + self.failed_tests}")
        print(f"🎯 Success Rate: {(self.passed_tests / (self.passed_tests + self.failed_tests) * 100):.1f}%")
        
        # Save detailed results
        with open("error_handling_test_results.json", "w") as f:
            json.dump({
                "test_summary": {
                    "passed": self.passed_tests,
                    "failed": self.failed_tests,
                    "total": self.passed_tests + self.failed_tests,
                    "success_rate": (self.passed_tests / (self.passed_tests + self.failed_tests) * 100)
                },
                "test_results": self.test_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📄 Detailed results saved to: error_handling_test_results.json")
        
        return self.failed_tests == 0

def main():
    """Main test runner"""
    tester = ErrorHandlingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Error handling is working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review the error handling implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
