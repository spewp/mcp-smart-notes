#!/usr/bin/env python3
"""
Simple MCP Note-Taking Server
"""
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

import mcp.types as types
from mcp.server import Server
import mcp.server.stdio

# Configuration
NOTES_DIR = Path.home() / "mcp-notes"
NOTES_DIR.mkdir(exist_ok=True)

app = Server("note-taking-server")

def get_note_path(note_id: str) -> Path:
    return NOTES_DIR / f"{note_id}.json"

def list_all_notes():
    notes = []
    for file in NOTES_DIR.glob("*.json"):
        try:
            with open(file, 'r') as f:
                note = json.load(f)
                notes.append(note)
        except json.JSONDecodeError:
            print(f"Warning: Could not read {file}", file=sys.stderr)
    return notes

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_note",
            description="Create a new note",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["title", "content"]
            }
        ),
        types.Tool(
            name="list_notes",
            description="List all notes",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "create_note":
        title = arguments.get("title", "")
        content = arguments.get("content", "")
        
        note_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        
        note_path = get_note_path(note_id)
        with open(note_path, 'w') as f:
            json.dump(note, f, indent=2)
        
        return [types.TextContent(
            type="text",
            text=f"Created note '{title}' with ID: {note_id}"
        )]
    
    elif name == "list_notes":
        notes = list_all_notes()
        if not notes:
            text = "No notes found."
        else:
            text = "Notes:\n" + "\n".join([
                f"- {note['title']} (ID: {note['id']})"
                for note in notes
            ])
        
        return [types.TextContent(
            type="text",
            text=text
        )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    async with mcp.server.stdio.stdio_server() as streams:
        await app.run(
            streams[0], 
            streams[1], 
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main()) 