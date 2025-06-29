#!/usr/bin/env python3
"""
Simple bridge demonstrating Ollama + Note System integration
This simulates MCP functionality without the complex protocol
WITH AUTOMATIC INTELLIGENT TAGGING
"""
import json
from datetime import datetime
from pathlib import Path
from ollama import Client

# Note system functions (simulating MCP tools)
NOTES_DIR = Path.home() / "mcp-notes"
NOTES_DIR.mkdir(exist_ok=True)

# Predefined tag categories for automatic assignment
AVAILABLE_TAGS = ["Greeting", "Coding", "Education", "Finance"]

def analyze_content_for_tags(title: str, content: str, client: Client, model: str = "qwen2.5:7b") -> list:
    """Use LLM to analyze content and automatically assign appropriate tags"""
    analysis_prompt = f"""
Analyze the following note and assign the most appropriate tags from this list: {', '.join(AVAILABLE_TAGS)}

Note Title: "{title}"
Note Content: "{content}"

Instructions:
- Only use tags from this exact list: {', '.join(AVAILABLE_TAGS)}
- Choose 1-3 most relevant tags
- Respond with ONLY a JSON array of tag names, nothing else
- Examples: ["Greeting"] or ["Coding", "Education"] or ["Finance"]

Tags:"""

    try:
        response = client.chat(
            model=model,
            messages=[{
                "role": "user", 
                "content": analysis_prompt
            }]
        )
        
        # Extract the response text
        response_text = (response.message.content or "").strip()
        
        # Try to parse as JSON
        try:
            suggested_tags = json.loads(response_text)
            # Validate that all tags are from our allowed list
            valid_tags = [tag for tag in suggested_tags if tag in AVAILABLE_TAGS]
            return valid_tags[:3]  # Limit to max 3 tags
        except json.JSONDecodeError:
            # Fallback: try to extract tags from text response
            found_tags = []
            for tag in AVAILABLE_TAGS:
                if tag.lower() in response_text.lower():
                    found_tags.append(tag)
            return found_tags[:2]  # Limit to max 2 tags for fallback
            
    except Exception as e:
        print(f"⚠️ Tag analysis failed: {e}")
        # Smart fallback based on keywords
        content_lower = (title + " " + content).lower()
        fallback_tags = []
        
        if any(word in content_lower for word in ["hello", "hi", "greetings", "welcome", "nice to meet"]):
            fallback_tags.append("Greeting")
        if any(word in content_lower for word in ["code", "python", "javascript", "programming", "function", "class", "api"]):
            fallback_tags.append("Coding")
        if any(word in content_lower for word in ["learn", "study", "education", "course", "tutorial", "lesson"]):
            fallback_tags.append("Education")
                          if any(word in content_lower for word in ["money", "budget", "finance", "investment", "cost", "price", "bank"]):
             fallback_tags.append("Finance")
             
         return fallback_tags[:2]  # Always return a list

def create_note(title: str, content: str, tags: list = None, auto_tag: bool = True) -> str:
    """Simulate MCP create_note tool with automatic intelligent tagging"""
    note_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    
    # Automatic tagging if enabled and no manual tags provided
    final_tags = tags if tags is not None else []
    
    if auto_tag and not final_tags:
        try:
            client = Client()
            auto_tags = analyze_content_for_tags(title, content, client)
            final_tags = auto_tags
            print(f"🏷️ Auto-assigned tags: {final_tags}")
        except Exception as e:
            print(f"⚠️ Auto-tagging failed: {e}")
    
    note = {
        "id": note_id,
        "title": title,
        "content": content,
        "tags": final_tags,
        "created_at": datetime.now().isoformat(),
        "auto_tagged": auto_tag and not tags  # Track if this was auto-tagged
    }
    
    note_path = NOTES_DIR / f"{note_id}.json"
    with open(note_path, 'w') as f:
        json.dump(note, f, indent=2)
    
    tag_info = f" with tags: {final_tags}" if final_tags else ""
    return f"✅ Created note '{title}' with ID: {note_id}{tag_info}"

def list_notes() -> str:
    """Simulate MCP list_notes tool"""
    notes = []
    for file in NOTES_DIR.glob("*.json"):
        try:
            with open(file, 'r') as f:
                note = json.load(f)
                notes.append(note)
        except json.JSONDecodeError:
            continue
    
    if not notes:
        return "No notes found."
    
    result = f"📚 Found {len(notes)} notes:\n"
    for note in sorted(notes, key=lambda x: x['created_at'], reverse=True):
        result += f"  - {note['title']} (ID: {note['id']})\n"
    return result

def search_notes(query: str) -> str:
    """Simulate MCP search_notes tool"""
    notes = []
    for file in NOTES_DIR.glob("*.json"):
        try:
            with open(file, 'r') as f:
                note = json.load(f)
                if (query.lower() in note.get('title', '').lower() or 
                    query.lower() in note.get('content', '').lower()):
                    notes.append(note)
        except json.JSONDecodeError:
            continue
    
    if not notes:
        return f"No notes found matching '{query}'"
    
    result = f"🔍 Found {len(notes)} note(s) matching '{query}':\n"
    for note in notes:
        result += f"  - {note['title']}: {note['content'][:50]}...\n"
    return result

def search_by_tag(tag: str) -> str:
    """Search notes by a specific tag"""
    notes = []
    for file in NOTES_DIR.glob("*.json"):
        try:
            with open(file, 'r') as f:
                note = json.load(f)
                if tag in note.get('tags', []):
                    notes.append(note)
        except json.JSONDecodeError:
            continue
    
    if not notes:
        return f"No notes found with tag '{tag}'"
    
    result = f"🏷️ Found {len(notes)} note(s) with tag '{tag}':\n"
    for note in sorted(notes, key=lambda x: x['created_at'], reverse=True):
        auto_tag_indicator = " 🤖" if note.get('auto_tagged', False) else ""
        result += f"  - {note['title']} (ID: {note['id']}){auto_tag_indicator}\n"
        result += f"    Tags: {', '.join(note.get('tags', []))}\n"
        result += f"    Content preview: {note['content'][:50]}...\n\n"
    return result

# Available "tools" for Ollama
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": f"Create a new note with title and content. Tags are automatically assigned by AI from: {', '.join(AVAILABLE_TAGS)}",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Note title"},
                    "content": {"type": "string", "description": "Note content"},
                    "tags": {
                        "type": "array", 
                        "items": {"type": "string"}, 
                        "description": f"Optional manual tags. If not provided, AI will auto-assign from: {', '.join(AVAILABLE_TAGS)}"
                    },
                    "auto_tag": {
                        "type": "boolean",
                        "description": "Whether to enable automatic tagging (default: true)",
                        "default": True
                    }
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "List all existing notes with their tags",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "Search for notes by title, content, or tags",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_tag",
            "description": f"Search notes by specific tags from: {', '.join(AVAILABLE_TAGS)}",
            "parameters": {
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "description": f"Tag to search for from: {', '.join(AVAILABLE_TAGS)}"}
                },
                "required": ["tag"]
            }
        }
    }
]

def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool call"""
    if tool_name == "create_note":
        return create_note(**arguments)
    elif tool_name == "list_notes":
        return list_notes()
    elif tool_name == "search_notes":
        return search_notes(**arguments)
    elif tool_name == "search_by_tag":
        return search_by_tag(**arguments)
    else:
        return f"Unknown tool: {tool_name}"

def chat_with_ollama(model="qwen2.5:7b"):
    """Interactive chat with Ollama using note-taking tools with auto-tagging"""
    client = Client()
    
    print(f"🤖 Starting chat with {model}")
    print("🏷️ AUTOMATIC TAGGING ENABLED!")
    print(f"Available tags: {', '.join(AVAILABLE_TAGS)}")
    print("\nI can help you manage your notes with intelligent auto-tagging. Try:")
    print("  - 'Create a note about my Python project ideas'")
    print("  - 'Create a note saying hello to my team' ")
    print("  - 'Create a note about my monthly budget'")
    print("  - 'Search notes by Coding tag'")
    print("  - 'List my notes'")
    print("Type 'quit' to exit.\n")
    
    messages = [{
        "role": "system",
        "content": f"""You are a helpful note-taking assistant with intelligent auto-tagging capabilities.

You have access to tools that can:
- create_note: Create new notes (AI automatically assigns tags from: {', '.join(AVAILABLE_TAGS)})
- list_notes: Show all existing notes with their tags
- search_notes: Find notes by searching title/content/tags
- search_by_tag: Find notes by specific tag

The automatic tagging system analyzes note content and assigns relevant tags from: {', '.join(AVAILABLE_TAGS)}

When users ask you to create notes, the system will automatically analyze the content and assign appropriate tags. Be helpful and mention when auto-tagging occurs."""
    }]
    
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
        
        if not user_input:
            continue
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            print("\n🤔 Thinking...", end="", flush=True)
            
            # Get response from Ollama with tools
            response = client.chat(
                model=model,
                messages=messages,
                tools=AVAILABLE_TOOLS
            )
            
            print("\r" + " " * 15 + "\r", end="")  # Clear "Thinking..."
            
            # Check if model wants to use tools
            if hasattr(response, 'message') and hasattr(response.message, 'tool_calls') and response.message.tool_calls:
                # Handle tool calls
                for tool_call in response.message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments
                    
                    print(f"🔧 Using tool: {tool_name}")
                    result = execute_tool(tool_name, tool_args)
                    print(f"Tool result: {result}")
                
                # Add tool results to conversation and get final response
                messages.append({"role": "assistant", "content": response.message.content or ""})
                messages.append({"role": "user", "content": f"Tool executed successfully. Here's the result: {result}"})
                
                final_response = client.chat(model=model, messages=messages)
                print(f"\nAssistant: {final_response.message.content}")
                messages.append({"role": "assistant", "content": final_response.message.content})
            else:
                # Regular response without tools
                content = response.message.content if hasattr(response, 'message') else str(response)
                print(f"Assistant: {content}")
                messages.append({"role": "assistant", "content": content})
                
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 MCP-Style Note System with Ollama + AUTO-TAGGING\n")
    
    # Check if Ollama is available
    try:
        client = Client()
        models = client.list()
        print(f"✅ Ollama connected with {len(models.models)} models")
        print(f"🏷️ Auto-tagging enabled with tags: {', '.join(AVAILABLE_TAGS)}")
        
        # Start the chat
        chat_with_ollama()
        
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running with: ollama serve") 