MCP NOTE-TAKING SYSTEM WITH INTELLIGENT AUTO-TAGGING
=====================================================

OVERVIEW
--------
This project implements a Model Context Protocol (MCP) compliant note-taking system 
with intelligent automatic tagging capabilities. The system demonstrates practical 
application of the MCP specification for resource management and tool integration 
with local Large Language Models (LLMs) via Ollama.

MCP PROTOCOL CONTEXT
--------------------
The Model Context Protocol is an open standard that enables secure, standardized 
communication between AI applications (hosts) and data/tool providers (servers). 
This implementation showcases three core MCP concepts:

1. Resources: Application-controlled data sources (note files)
2. Tools: Model-controlled executable functions (create, search, manage notes)
3. Prompts: User-controlled templates and interaction patterns

Communication occurs via JSON-RPC 2.0 over stdio transport, adhering to the 
official MCP specification available at: https://modelcontextprotocol.io

ARCHITECTURE
------------
The system consists of four primary components:

1. MCP Server Implementation (note_server.py, simple_note_server.py)
2. MCP Client Bridge (ollama_mcp_client.py)
3. Intelligent Auto-Tagging Bridge (smart_tagging_bridge.py)
4. Simplified Integration Layer (simple_bridge.py)

COMPONENTS
----------

note_server.py
- Full MCP server implementation with complete tool set
- Supports: create_note, search_notes, list_recent_notes, get_note, update_note, delete_note
- Implements MCP resource discovery and JSON-RPC communication
- Provides structured data persistence using JSON file format

simple_note_server.py  
- Minimal MCP server implementation for basic functionality
- Reduced feature set for testing and development
- Demonstrates core MCP server patterns

ollama_mcp_client.py
- MCP client implementation for Ollama integration
- Handles protocol negotiation and tool execution
- Bridges MCP servers with local LLM instances

smart_tagging_bridge.py
- Advanced implementation with intelligent auto-tagging
- Utilizes LLM analysis for semantic content categorization
- Supports predefined tag categories: Greeting, Coding, Education, Finance
- Implements fallback keyword-based tagging for robustness

simple_bridge.py
- Direct integration approach bypassing full MCP protocol complexity
- Simulates MCP functionality for rapid prototyping
- Suitable for development and testing scenarios

test_auto_tagging.py
- Validation script for automatic tagging functionality
- Demonstrates system capabilities with test data sets
- Provides verification of LLM-based tag assignment

TECHNICAL SPECIFICATIONS
-------------------------

Data Storage:
- JSON file format in user home directory (~/.mcp-notes/)
- Atomic file operations with timestamp-based unique identifiers
- Metadata tracking including creation time, modification time, and auto-tag indicators

Tag Categories:
- Predefined taxonomy: ["Greeting", "Coding", "Education", "Finance"]
- LLM-driven semantic analysis for automatic assignment
- Multi-tag support with maximum limits (3 auto-assigned, 2 fallback)
- Keyword-based fallback classification system

Communication Protocol:
- JSON-RPC 2.0 over stdio transport
- Structured tool definitions with parameter validation
- Error handling and graceful degradation
- Session management and connection lifecycle

INSTALLATION
------------
1. Install required dependencies:
   pip install -r requirements.txt

2. Ensure Ollama is installed and running:
   ollama serve

3. Verify Ollama models are available (tested with qwen2.5:7b, gemma:2b)

USAGE
-----

Basic MCP Server:
python simple_note_server.py

Full MCP Server:
python note_server.py

Intelligent Auto-Tagging System:
python smart_tagging_bridge.py

Simplified Integration:
python simple_bridge.py

Auto-Tagging Validation:
python test_auto_tagging.py

SYSTEM REQUIREMENTS
-------------------
- Python 3.8+
- Ollama runtime environment
- Compatible LLM models (qwen2.5:7b recommended)
- File system write access for note storage

MCP SPECIFICATION COMPLIANCE
-----------------------------
This implementation adheres to the Model Context Protocol specification version 2024-11-05.
Key compliance areas:
- Tool registration and parameter schemas
- Resource discovery and URI handling  
- JSON-RPC 2.0 message structure
- Error handling and status codes
- Transport layer abstraction

REFERENCES
----------
1. Model Context Protocol Specification: https://modelcontextprotocol.io
2. MCP TypeScript SDK Documentation: https://github.com/modelcontextprotocol/typescript-sdk
3. Ollama Documentation: https://ollama.ai/
4. JSON-RPC 2.0 Specification: https://www.jsonrpc.org/specification

TECHNICAL NOTES
---------------
- Auto-tagging utilizes structured prompts for LLM analysis
- Fallback mechanisms ensure system reliability
- File-based persistence provides simplicity and portability
- Unicode support for international content
- Atomic operations prevent data corruption
- Extensible architecture supports additional tag categories and tools

This implementation serves as a practical demonstration of MCP protocol capabilities
and provides a foundation for building more complex AI-integrated applications. 