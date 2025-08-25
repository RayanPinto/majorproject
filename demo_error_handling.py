#!/usr/bin/env python3
"""
Error Handling Demonstration Script
Shows all error handling features in action with various test scenarios
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import (
    StateManagementError, ValidationError, JSONProcessingError, 
    StateUpdateError, DatabaseError, UserInputError,
    validate_json_structure, validate_user_input, format_error_response,
    log_error
)

class ErrorHandlingDemo:
    """Demonstration of error handling features"""
    
    def __init__(self):
        self.demo_results = []
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_result(self, scenario: str, result: str, success: bool = True):
        """Print a formatted result"""
        status = "✅" if success else "❌"
        print(f"{status} {scenario}")
        print(f"   Result: {result}")
        print()
        
        self.demo_results.append({
            "scenario": scenario,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    def demo_exception_classes(self):
        """Demonstrate custom exception classes"""
        self.print_header("Custom Exception Classes")
        
        # Test base exception
        try:
            raise StateManagementError("Demo base error", "DEMO_001", {"demo": True})
        except StateManagementError as e:
            self.print_result("Base Exception", f"Error code: {e.error_code}, Details: {e.details}")
        
        # Test validation error
        try:
            raise ValidationError("Demo validation error", "VAL_001")
        except ValidationError as e:
            self.print_result("Validation Exception", f"Message: {e.message}")
        
        # Test JSON processing error
        try:
            raise JSONProcessingError("Demo JSON error", "JSON_001", {"json": "demo"})
        except JSONProcessingError as e:
            self.print_result("JSON Processing Exception", f"Details: {e.details}")
    
    def demo_json_validation(self):
        """Demonstrate JSON validation"""
        self.print_header("JSON Structure Validation")
        
        template_keys = ["_id", "user_id", "jwt"]
        
        # Valid JSON
        valid_json = {"_id": "123", "user_id": "user1", "jwt": "token123"}
        result = validate_json_structure(valid_json, template_keys)
        self.print_result("Valid JSON", f"Valid: {result['valid']}, Warnings: {result['warnings']}")
        
        # Missing keys
        missing_keys_json = {"_id": "123", "user_id": "user1"}
        result = validate_json_structure(missing_keys_json, template_keys)
        self.print_result("Missing Keys", f"Valid: {result['valid']}, Warnings: {result['warnings']}")
        
        # Extra keys
        extra_keys_json = {"_id": "123", "user_id": "user1", "jwt": "token123", "extra": "value"}
        result = validate_json_structure(extra_keys_json, template_keys)
        self.print_result("Extra Keys", f"Valid: {result['valid']}, Warnings: {result['warnings']}")
        
        # Invalid data types
        invalid_types_json = {"_id": "123", "user_id": ["invalid"], "jwt": "token123"}
        result = validate_json_structure(invalid_types_json, template_keys)
        self.print_result("Invalid Data Types", f"Valid: {result['valid']}, Errors: {result['errors']}", False)
        
        # Empty JSON
        empty_json = {}
        result = validate_json_structure(empty_json, template_keys)
        self.print_result("Empty JSON", f"Valid: {result['valid']}, Warnings: {result['warnings']}")
    
    def demo_user_input_validation(self):
        """Demonstrate user input validation"""
        self.print_header("User Input Validation")
        
        # Valid JSON command
        valid_json_cmd = 'Process this JSON: {"_id": "123", "user_id": "user1"}'
        result = validate_user_input(valid_json_cmd)
        self.print_result("Valid JSON Command", f"Valid: {result['valid']}")
        
        # Invalid JSON command
        invalid_json_cmd = 'Process this JSON: {"_id": "123", "user_id":}'
        result = validate_user_input(invalid_json_cmd)
        self.print_result("Invalid JSON Command", f"Valid: {result['valid']}, Errors: {result['errors']}", False)
        
        # Empty JSON command
        empty_json_cmd = "Process this JSON:"
        result = validate_user_input(empty_json_cmd)
        self.print_result("Empty JSON Command", f"Valid: {result['valid']}, Errors: {result['errors']}", False)
        
        # Valid update command
        valid_update_cmd = "Update state: _id=123"
        result = validate_user_input(valid_update_cmd)
        self.print_result("Valid Update Command", f"Valid: {result['valid']}")
        
        # Invalid update command
        invalid_update_cmd = "Update state:"
        result = validate_user_input(invalid_update_cmd)
        self.print_result("Invalid Update Command", f"Valid: {result['valid']}, Errors: {result['errors']}", False)
        
        # Update command without equals
        no_equals_cmd = "Update state: _id 123"
        result = validate_user_input(no_equals_cmd)
        self.print_result("Update Command No Equals", f"Valid: {result['valid']}, Errors: {result['errors']}", False)
        
        # Empty command
        empty_cmd = ""
        result = validate_user_input(empty_cmd)
        self.print_result("Empty Command", f"Valid: {result['valid']}, Errors: {result['errors']}", False)
    
    def demo_error_response_formatting(self):
        """Demonstrate error response formatting"""
        self.print_header("Error Response Formatting")
        
        # Validation error
        val_error = ValidationError("Demo validation error", "VAL_001")
        response = format_error_response(val_error)
        self.print_result("Validation Error Formatting", response)
        
        # JSON processing error
        json_error = JSONProcessingError("Demo JSON error", "JSON_001")
        response = format_error_response(json_error)
        self.print_result("JSON Error Formatting", response)
        
        # State update error
        state_error = StateUpdateError("Demo state error", "STATE_001")
        response = format_error_response(state_error)
        self.print_result("State Error Formatting", response)
        
        # Database error
        db_error = DatabaseError("Demo database error", "DB_001")
        response = format_error_response(db_error)
        self.print_result("Database Error Formatting", response)
        
        # User input error
        input_error = UserInputError("Demo input error", "INPUT_001")
        response = format_error_response(input_error)
        self.print_result("Input Error Formatting", response)
        
        # Generic error
        generic_error = Exception("Demo generic error")
        response = format_error_response(generic_error)
        self.print_result("Generic Error Formatting", response)
        
        # Technical error formatting
        tech_error = ValidationError("Technical error", "TECH_001")
        response = format_error_response(tech_error, user_friendly=False)
        self.print_result("Technical Error Formatting", response)
    
    def demo_edge_cases(self):
        """Demonstrate edge cases"""
        self.print_header("Edge Cases and Boundary Conditions")
        
        # Very large JSON
        large_json = {"_id": "x" * 100, "user_id": "y" * 100, "jwt": "z" * 100}
        result = validate_json_structure(large_json, ["_id", "user_id", "jwt"])
        self.print_result("Large JSON Values", f"Valid: {result['valid']}")
        
        # Special characters in JSON
        special_chars_json = {"_id": "test\n\t\r", "user_id": "test\"'\\", "jwt": "test{}[]"}
        result = validate_json_structure(special_chars_json, ["_id", "user_id", "jwt"])
        self.print_result("Special Characters JSON", f"Valid: {result['valid']}")
        
        # Numeric values
        numeric_json = {"_id": 123, "user_id": 456, "jwt": "token"}
        result = validate_json_structure(numeric_json, ["_id", "user_id", "jwt"])
        self.print_result("Numeric Values JSON", f"Valid: {result['valid']}")
        
        # Boolean values
        boolean_json = {"_id": True, "user_id": False, "jwt": "token"}
        result = validate_json_structure(boolean_json, ["_id", "user_id", "jwt"])
        self.print_result("Boolean Values JSON", f"Valid: {result['valid']}")
        
        # Null values
        null_json = {"_id": None, "user_id": "user1", "jwt": None}
        result = validate_json_structure(null_json, ["_id", "user_id", "jwt"])
        self.print_result("Null Values JSON", f"Valid: {result['valid']}")
        
        # Empty string values
        empty_strings_json = {"_id": "", "user_id": "", "jwt": ""}
        result = validate_json_structure(empty_strings_json, ["_id", "user_id", "jwt"])
        self.print_result("Empty String Values JSON", f"Valid: {result['valid']}")
    
    def demo_malformed_inputs(self):
        """Demonstrate malformed input handling"""
        self.print_header("Malformed Input Handling")
        
        # Malformed JSON strings
        malformed_inputs = [
            'Process this JSON: {"_id": "123",}',  # Trailing comma
            'Process this JSON: {"_id": "123"',    # Missing closing brace
            'Process this JSON: {_id: "123"}',     # Missing quotes
            'Process this JSON: {"_id": 123,}',    # Trailing comma with number
            'Process this JSON: {"_id": "123", "user_id":}',  # Incomplete value
        ]
        
        for i, malformed_input in enumerate(malformed_inputs):
            result = validate_user_input(malformed_input)
            self.print_result(f"Malformed JSON {i+1}", f"Valid: {result['valid']}, Errors: {result['errors']}", False)
        
        # Malformed update commands
        malformed_updates = [
            "Update state: =value",           # Empty key
            "Update state: key=",             # Empty value
            "Update state: key value",        # No equals
            "Update state: key=value extra",  # Extra text
            "Update state:",                  # No key-value
        ]
        
        for i, malformed_update in enumerate(malformed_updates):
            result = validate_user_input(malformed_update)
            self.print_result(f"Malformed Update {i+1}", f"Valid: {result['valid']}, Errors: {result['errors']}", False)
    
    def demo_error_logging(self):
        """Demonstrate error logging"""
        self.print_header("Error Logging and Context")
        
        # Log various types of errors
        try:
            raise ValidationError("Demo validation error", "VAL_001", {"field": "user_id"})
        except ValidationError as e:
            error_info = log_error(e, "Demo Validation", {"user_input": "test input"})
            self.print_result("Validation Error Logging", f"Logged with context: {error_info['context']}")
        
        try:
            raise JSONProcessingError("Demo JSON error", "JSON_001", {"json_string": "invalid json"})
        except JSONProcessingError as e:
            error_info = log_error(e, "Demo JSON Processing", {"file": "test.json"})
            self.print_result("JSON Error Logging", f"Logged with context: {error_info['context']}")
        
        try:
            raise DatabaseError("Demo database error", "DB_001", {"connection": "mongodb"})
        except DatabaseError as e:
            error_info = log_error(e, "Demo Database", {"operation": "insert"})
            self.print_result("Database Error Logging", f"Logged with context: {error_info['context']}")
    
    def run_demo(self):
        """Run all demonstrations"""
        print("🚀 Starting Error Handling Demonstration")
        print("This demo shows all error handling features in action")
        
        self.demo_exception_classes()
        self.demo_json_validation()
        self.demo_user_input_validation()
        self.demo_error_response_formatting()
        self.demo_edge_cases()
        self.demo_malformed_inputs()
        self.demo_error_logging()
        
        # Print summary
        print(f"\n{'='*60}")
        print("📊 DEMONSTRATION SUMMARY")
        print(f"{'='*60}")
        print(f"🎯 Total Scenarios: {len(self.demo_results)}")
        print(f"✅ Successful: {sum(1 for r in self.demo_results if r['success'])}")
        print(f"❌ Failed: {sum(1 for r in self.demo_results if not r['success'])}")
        
        # Save demo results
        with open("error_handling_demo_results.json", "w") as f:
            json.dump({
                "demo_summary": {
                    "total_scenarios": len(self.demo_results),
                    "successful": sum(1 for r in self.demo_results if r['success']),
                    "failed": sum(1 for r in self.demo_results if not r['success'])
                },
                "demo_results": self.demo_results,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📄 Demo results saved to: error_handling_demo_results.json")
        print("\n🎉 Error handling demonstration completed successfully!")

def main():
    """Main demo runner"""
    demo = ErrorHandlingDemo()
    demo.run_demo()

if __name__ == "__main__":
    main()

