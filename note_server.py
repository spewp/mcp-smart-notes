#!/usr/bin/env python3
"""
MCP Note-Taking Server
A simple server for managing personal notes with search capabilities
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import mcp.types as types
from mcp.server import Server
import mcp.server.stdio

# Configuration
NOTES_DIR = Path.home() / "mcp-notes"
NOTES_DIR.mkdir(exist_ok=True)

# Initialize the MCP server
app = Server("note-taking-server")

# Helper functions
def get_note_path(note_id: str) -> Path:
    """Get the file path for a note by ID"""
    return NOTES_DIR / f"{note_id}.json"

def list_all_notes() -> List[Dict]:
    """List all notes from the storage directory"""
    notes = []
    for file in NOTES_DIR.glob("*.json"):
        try:
            with open(file, 'r') as f:
                note = json.load(f)
                notes.append(note)
        except json.JSONDecodeError:
            print(f"Warning: Could not read {file}", file=sys.stderr)
    return notes

def search_notes_by_content(query: str) -> List[Dict]:
    """Search notes by content, title, or tags"""
    results = []
    query_lower = query.lower()
    for note in list_all_notes():
        if (query_lower in note.get('content', '').lower() or 
            query_lower in note.get('title', '').lower() or 
            any(query_lower in tag.lower() for tag in note.get('tags', []))):
            results.append(note)
    return results

# Resource handlers
@app.list_resources()
async def list_resources() -> list[types.Resource]:
    """List all notes as MCP resources"""
    notes = list_all_notes()
    return [
        types.Resource(
            uri=f"note:///{note['id']}",
            name=note['title'],
            mimeType="text/markdown",
            description=f"Note created on {note['created_at']}"
        )
        for note in notes
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a specific note resource"""
    note_id = uri.replace("note:///", "")
    note_path = get_note_path(note_id)
    
    if note_path.exists():
        with open(note_path, 'r') as f:
            note = json.load(f)
            content = f"# {note['title']}\n\n"
            content += f"{note['content']}\n\n"
            content += f"---\n"
            content += f"Created: {note['created_at']}\n"
            content += f"Updated: {note['updated_at']}\n"
            if note.get('tags'):
                content += f"Tags: {', '.join(note['tags'])}\n"
            return content
    else:
        raise ValueError(f"Note {note_id} not found")

# Tool handlers
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="create_note",
            description="Create a new note with title, content, and optional tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Note title"},
                    "content": {"type": "string", "description": "Note content"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for the note"
                    }
                },
                "required": ["title", "content"]
            }
        ),
        types.Tool(
            name="search_notes",
            description="Search notes by content, title, or tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="list_recent_notes",
            description="List the most recent notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of notes to return", "default": 10}
                }
            }
        ),
        types.Tool(
            name="get_note",
            description="Get the full content of a specific note",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "string", "description": "Note ID"}
                },
                "required": ["note_id"]
            }
        ),
        types.Tool(
            name="update_note",
            description="Update an existing note's title, content, or tags",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "string", "description": "Note ID"},
                    "title": {"type": "string", "description": "New title"},
                    "content": {"type": "string", "description": "New content"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags"
                    }
                },
                "required": ["note_id"]
            }
        ),
        types.Tool(
            name="delete_note",
            description="Delete a note by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "string", "description": "Note ID"}
                },
                "required": ["note_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    if name == "create_note":
        return await handle_create_note(**arguments)
    elif name == "search_notes":
        return await handle_search_notes(**arguments)
    elif name == "list_recent_notes":
        return await handle_list_recent_notes(**arguments)
    elif name == "get_note":
        return await handle_get_note(**arguments)
    elif name == "update_note":
        return await handle_update_note(**arguments)
    elif name == "delete_note":
        return await handle_delete_note(**arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

# Tool implementation functions
async def handle_create_note(title: str, content: str, tags: Optional[List[str]] = None) -> list[types.TextContent]:
    """Create a new note with title, content, and optional tags."""
    note_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
    note = {
        "id": note_id,
        "title": title,
        "content": content,
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    note_path = get_note_path(note_id)
    with open(note_path, 'w') as f:
        json.dump(note, f, indent=2)
    
    return f"✅ Note created successfully!\nID: {note_id}\nTitle: {title}"

@app.tool()
async def search_notes(query: str) -> str:
    """Search notes by content, title, or tags."""
    results = search_notes_by_content(query)
    
    if not results:
        return f"No notes found matching '{query}'"
    
    output = f"Found {len(results)} note(s) matching '{query}':\n\n"
    for note in results:
        output += f"📝 {note['title']} (ID: {note['id']})\n"
        preview = note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
        output += f"   {preview}\n"
        if note.get('tags'):
            output += f"   Tags: {', '.join(note['tags'])}\n"
        output += "\n"
    
    return output

@app.tool()
async def update_note(note_id: str, title: Optional[str] = None, 
                     content: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    """Update an existing note's title, content, or tags."""
    note_path = get_note_path(note_id)
    
    if not note_path.exists():
        return f"❌ Note {note_id} not found"
    
    with open(note_path, 'r') as f:
        note = json.load(f)
    
    # Track what was updated
    updates = []
    if title is not None:
        note['title'] = title
        updates.append("title")
    if content is not None:
        note['content'] = content
        updates.append("content")
    if tags is not None:
        note['tags'] = tags
        updates.append("tags")
    
    if updates:
        note['updated_at'] = datetime.now().isoformat()
        
        with open(note_path, 'w') as f:
            json.dump(note, f, indent=2)
        
        return f"✅ Note {note_id} updated successfully!\nUpdated: {', '.join(updates)}"
    else:
        return "ℹ️ No updates provided"

@app.tool()
async def list_recent_notes(limit: int = 10) -> str:
    """List the most recent notes."""
    notes = sorted(list_all_notes(), 
                  key=lambda x: x['created_at'], 
                  reverse=True)[:limit]
    
    if not notes:
        return "No notes found. Create your first note!"
    
    output = f"📚 Recent notes (showing up to {limit}):\n\n"
    for i, note in enumerate(notes, 1):
        output += f"{i}. {note['title']} (ID: {note['id']})\n"
        output += f"   Created: {note['created_at'][:10]}\n"
        if note.get('tags'):
            output += f"   Tags: {', '.join(note['tags'])}\n"
        output += "\n"
    
    return output

@app.tool()
async def get_note(note_id: str) -> str:
    """Get the full content of a specific note."""
    note_path = get_note_path(note_id)
    
    if not note_path.exists():
        return f"❌ Note {note_id} not found"
    
    with open(note_path, 'r') as f:
        note = json.load(f)
    
    output = f"📝 {note['title']}\n"
    output += f"{'=' * len(note['title'])}\n\n"
    output += f"{note['content']}\n\n"
    output += f"---\n"
    output += f"ID: {note['id']}\n"
    output += f"Created: {note['created_at']}\n"
    output += f"Updated: {note['updated_at']}\n"
    if note.get('tags'):
        output += f"Tags: {', '.join(note['tags'])}\n"
    
    return output

@app.tool()
async def delete_note(note_id: str) -> str:
    """Delete a note by ID."""
    note_path = get_note_path(note_id)
    
    if not note_path.exists():
        return f"❌ Note {note_id} not found"
    
    # Read note info before deletion
    with open(note_path, 'r') as f:
        note = json.load(f)
        title = note['title']
    
    # Delete the file
    note_path.unlink()
    
    return f"🗑️ Note '{title}' (ID: {note_id}) deleted successfully"

# Run the server
async def main():
    async with mcp.server.stdio.stdio_server() as streams:
        await app.run(
            streams[0], 
            streams[1], 
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main()) 