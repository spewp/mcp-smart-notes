#!/usr/bin/env python3
"""
Test script for automatic tagging functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from smart_tagging_bridge import create_note, search_by_tag, list_notes, AVAILABLE_TAGS
from ollama import Client

def test_auto_tagging():
    """Test the automatic tagging system with various note types"""
    print("🧪 Testing Automatic Tagging System")
    print(f"Available tags: {', '.join(AVAILABLE_TAGS)}")
    print("=" * 50)
    
    # Test notes with different content types
    test_notes = [
        {
            "title": "Morning Greeting",
            "content": "Hello everyone! Hope you all have a wonderful day ahead. Nice to see you all!"
        },
        {
            "title": "Python Web API Project",
            "content": "Building a REST API using FastAPI. Need to implement authentication, database connections, and error handling."
        },
        {
            "title": "Learning Machine Learning",
            "content": "Started studying neural networks and deep learning. Planning to take an online course on TensorFlow."
        },
        {
            "title": "Monthly Budget Review",
            "content": "Need to review expenses for this month. Check bank statements, investment portfolio, and savings goals."
        }
    ]
    
    print("\n🔬 Creating test notes with auto-tagging...\n")
    
    created_notes = []
    for i, note_data in enumerate(test_notes, 1):
        print(f"Test {i}: Creating note '{note_data['title']}'")
        try:
            result = create_note(
                title=note_data["title"],
                content=note_data["content"],
                auto_tag=True
            )
            print(f"✅ {result}")
            created_notes.append(note_data["title"])
        except Exception as e:
            print(f"❌ Failed: {e}")
        print()
    
    print("=" * 50)
    print("\n📚 Listing all notes:")
    print(list_notes())
    
    print("\n🏷️ Testing tag-based search:")
    for tag in AVAILABLE_TAGS:
        print(f"\nSearching for '{tag}' tagged notes:")
        result = search_by_tag(tag)
        print(result)

def test_ollama_connection():
    """Test if Ollama is available for auto-tagging"""
    try:
        client = Client()
        models = client.list()
        print(f"✅ Ollama connected with {len(models.models)} models")
        return True
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("Auto-tagging will use keyword fallback method")
        return False

if __name__ == "__main__":
    print("🚀 Auto-Tagging Test Suite")
    print()
    
    # Test Ollama connection
    ollama_available = test_ollama_connection()
    print()
    
    # Run auto-tagging tests
    test_auto_tagging()
    
    print("\n" + "=" * 50)
    print("✅ Auto-tagging test completed!")
    if ollama_available:
        print("💡 You can now run: python smart_tagging_bridge.py")
    else:
        print("⚠️ Start Ollama first: ollama serve") 