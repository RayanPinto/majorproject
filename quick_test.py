#!/usr/bin/env python3
"""
Quick Test Script
Quick verification that the system is working before comprehensive testing.
"""

def test_system_components():
    """Test that all system components are working"""
    print("🔍 Quick System Test")
    print("=" * 40)
    
    try:
        # Test imports
        from manager.agent import state_manager_agent
        print("✅ Main agent imported successfully")
        
        from manager.sub_agents.state_agent import state_agent
        print("✅ State agent imported successfully")
        
        from manager.sub_agents.conversational_agent import conversational_agent
        print("✅ Conversational agent imported successfully")
        
        from utils import process_state_updates, display_state
        print("✅ Utility functions imported successfully")
        
        # Test intent classification
        from manager.agent import classify_query
        
        test_queries = [
            "append this query",
            "update my user_id to john_doe", 
            "show me my current state",
            "help me",
            "hello there"
        ]
        
        print("\n🧠 Testing Intent Classification:")
        for query in test_queries:
            intent = classify_query(query)
            print(f"  '{query}' → {intent}")
        
        print("\n✅ All system components are working!")
        print("🎉 Ready for comprehensive testing!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("⚠️ System needs fixing before testing")
        return False

def show_test_instructions():
    """Show instructions for testing"""
    print("\n" + "=" * 40)
    print("📋 TESTING INSTRUCTIONS")
    print("=" * 40)
    print()
    print("1. Run the system:")
    print("   python main.py")
    print()
    print("2. Test with these sample queries:")
    print("   • 'hi' (greeting)")
    print("   • 'help me' (help request)")
    print("   • 'show me my current state' (info request)")
    print("   • 'Process this JSON: {\"_id\": \"test\", \"user_id\": \"user\", \"jwt\": \"token\"}' (JSON processing)")
    print("   • 'update my user_id to john_doe' (state update)")
    print()
    print("3. For comprehensive testing, run:")
    print("   python test_comprehensive_queries.py")
    print()

if __name__ == "__main__":
    success = test_system_components()
    if success:
        show_test_instructions()
    else:
        print("\n❌ Please fix the system issues before testing.")




