#!/usr/bin/env python3
"""
Ollama MCP Bridge Client
Connects Ollama to MCP servers for tool-enabled conversations
"""
import asyncio
import json
import sys
from typing import Dict, List, Optional
from contextlib import AsyncExitStack
from ollama import Client as OllamaClient
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

class OllamaMCPBridge:
    def __init__(self, model_name: str = "llama3.2"):
        self.ollama = OllamaClient()
        self.model = model_name
        self.session = None
        self.tools = []
        self.exit_stack = AsyncExitStack()
        
    async def connect_to_server(self, server_path: str):
        """Connect to the MCP server"""
        print(f"🔌 Connecting to MCP server: {server_path}")
        
        server_params = StdioServerParameters(
            command="python" if sys.platform != "win32" else "python.exe",
            args=[server_path]
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.read, self.write = stdio_transport
        
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.read, self.write)
        )
        
        await self.session.initialize()
        
        # Get available tools
        tools_result = await self.session.list_tools()
        self.tools = tools_result.tools
        print(f"✅ Connected to server with tools: {[t.name for t in self.tools]}")
        
        # Get available resources
        resources_result = await self.session.list_resources()
        if resources_result.resources:
            print(f"📚 Available resources: {[r.name for r in resources_result.resources]}")
    
    def tools_to_ollama_format(self) -> List[Dict]:
        """Convert MCP tools to Ollama function format"""
        ollama_tools = []
        for tool in self.tools:
            # Convert the inputSchema to proper format
            parameters = {}
            if hasattr(tool.inputSchema, 'properties'):
                parameters = {
                    "type": "object",
                    "properties": tool.inputSchema.properties,
                    "required": getattr(tool.inputSchema, 'required', [])
                }
            
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Tool: {tool.name}",
                    "parameters": parameters
                }
            })
        return ollama_tools
    
    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool and return the result as a string"""
        try:
            result = await self.session.call_tool(tool_name, arguments)
            
            # Extract text content from the result
            if hasattr(result, 'content'):
                text_parts = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        text_parts.append(content.text)
                    elif hasattr(content, 'type') and content.type == 'text':
                        text_parts.append(str(content))
                return '\n'.join(text_parts)
            
            return str(result)
        except Exception as e:
            return f"Error calling tool {tool_name}: {str(e)}"
    
    async def chat_loop(self):
        """Interactive chat loop"""
        print("\n📝 Note-Taking Assistant Ready!")
        print("I can help you create, search, and manage your notes.")
        print("Type 'quit' to exit.\n")
        
        messages = []
        
        # System prompt
        system_prompt = """You are a helpful note-taking assistant. You have access to tools that can:
- Create new notes with titles, content, and tags
- Search for existing notes by content, title, or tags
- List recent notes
- Get full content of specific notes
- Update existing notes
- Delete notes

When a user asks you to perform any of these actions, use the appropriate tool.
Be concise but friendly in your responses."""
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nGoodbye! 👋")
                    break
                
                if not user_input:
                    continue
                
                messages.append({"role": "user", "content": user_input})
                
                # Get response from Ollama with tools
                print("\n🤔 Thinking...", end='', flush=True)
                
                response = self.ollama.chat(
                    model=self.model,
                    messages=[{"role": "system", "content": system_prompt}] + messages,
                    tools=self.tools_to_ollama_format(),
                    stream=False
                )
                
                print("\r", end='')  # Clear the "Thinking..." message
                
                # Check if Ollama wants to use a tool
                if hasattr(response, 'message') and hasattr(response.message, 'tool_calls') and response.message.tool_calls:
                    # Process tool calls
                    tool_results = []
                    
                    for tool_call in response.message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = tool_call.function.arguments
                        
                        print(f"🔧 Using tool: {tool_name}")
                        if isinstance(tool_args, str):
                            try:
                                tool_args = json.loads(tool_args)
                            except:
                                tool_args = {}
                        
                        # Call the MCP tool
                        result = await self.call_tool(tool_name, tool_args)
                        tool_results.append({
                            "tool_call_id": getattr(tool_call, 'id', tool_name),
                            "result": result
                        })
                    
                    # Add assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": response.message.content or "",
                        "tool_calls": response.message.tool_calls
                    })
                    
                    # Add tool results
                    for result in tool_results:
                        messages.append({
                            "role": "tool",
                            "content": result["result"]
                        })
                    
                    # Get final response from Ollama after tool use
                    final_response = self.ollama.chat(
                        model=self.model,
                        messages=[{"role": "system", "content": system_prompt}] + messages,
                        stream=False
                    )
                    
                    print(f"\nAssistant: {final_response.message.content}")
                    messages.append({
                        "role": "assistant", 
                        "content": final_response.message.content
                    })
                else:
                    # Regular response without tool usage
                    content = response.message.content if hasattr(response, 'message') else str(response)
                    print(f"\nAssistant: {content}")
                    messages.append({"role": "assistant", "content": content})
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'quit' to exit.")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try again.")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python ollama_mcp_client.py <path_to_server.py> [model_name]")
        print("Example: python ollama_mcp_client.py ./note_server.py llama3.2")
        sys.exit(1)
    
    server_path = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "llama3.2"
    
    # Check if Ollama is running
    try:
        test_client = OllamaClient()
        test_client.list()
    except Exception as e:
        print("❌ Error: Cannot connect to Ollama. Make sure Ollama is running.")
        print("   Run 'ollama serve' in another terminal.")
        sys.exit(1)
    
    bridge = OllamaMCPBridge(model_name=model_name)
    
    try:
        await bridge.connect_to_server(server_path)
        await bridge.chat_loop()
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
    finally:
        await bridge.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 