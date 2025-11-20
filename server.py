from flask import Flask, request, jsonify, Response
import json
import os
from datetime import datetime
import time

app = Flask(__name__)

# CORS header'ları nginx tarafından yönetiliyor
# Flask-CORS kullanmıyoruz çünkü nginx zaten tüm CORS header'larını ekliyor

# MCP Server bilgileri
SERVER_INFO = {
    "name": "ZZeti-MCP-Server",
    "version": "1.0.0"
}

# Basit tool'lar - ZZeti'ye özel
TOOLS = [
    {
        "name": "echo",
        "description": "Echo back the input text",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to echo back"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "add",
        "description": "Add two numbers",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "First number"
                },
                "b": {
                    "type": "number",
                    "description": "Second number"
                }
            },
            "required": ["a", "b"]
        }
    },
    {
        "name": "get_time",
        "description": "Get current time",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "zzeti_info",
        "description": "Get information about ZZeti platform",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "server": SERVER_INFO})


# MCP endpoint - ana endpoint
@app.route('/mcp', methods=['GET', 'POST', 'OPTIONS'])
def mcp():
    # OPTIONS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    # GET isteği için (health check vb.)
    if request.method == 'GET':
        return jsonify({
            "jsonrpc": "2.0",
            "result": {
                "serverInfo": SERVER_INFO,
                "status": "ok"
            }
        })
    
    # POST isteği için (MCP protokolü)
    try:
        # JSON parse
        if not request.is_json:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error: Content-Type must be application/json"
                }
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error: Invalid JSON"
                }
            }), 400
        
        # JSON-RPC 2.0 validation
        if data.get("jsonrpc") != "2.0":
            return jsonify({
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: jsonrpc must be '2.0'"
                }
            }), 400
        
        method = data.get('method')
        params = data.get('params', {})
        request_id = data.get('id')
        
        # Method kontrolü
        if not method:
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: 'method' is required"
                }
            }), 400

        # MCP Methods
        if method == 'initialize':
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": SERVER_INFO
                }
            })

        elif method == 'tools/list':
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": TOOLS
                }
            })

        elif method == 'tools/call':
            tool_name = params.get('name') if isinstance(params, dict) else None
            tool_args = params.get('arguments', {}) if isinstance(params, dict) else {}
            
            if not tool_name:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32602,
                        "message": "Invalid params: 'name' is required"
                    }
                }), 400

            result = None
            if tool_name == 'echo':
                result = {"text": tool_args.get('text', '')}
            elif tool_name == 'add':
                a = tool_args.get('a', 0) or 0
                b = tool_args.get('b', 0) or 0
                result = {"sum": float(a) + float(b)}
            elif tool_name == 'get_time':
                result = {"time": datetime.now().isoformat()}
            elif tool_name == 'zzeti_info':
                result = {
                    "platform": "ZZeti",
                    "description": "ZZeti MCP Platform - Model Context Protocol Server",
                    "version": SERVER_INFO["version"],
                    "features": ["MCP Protocol", "HTTP Transport", "Tool Support"]
                }
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                }), 400

            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            })

        else:
            return jsonify({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }), 400

    except json.JSONDecodeError as e:
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        }), 400
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in /mcp endpoint: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.get_json().get('id') if request.is_json and request.get_json() else None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }), 500


# SSE endpoint - inspector için
@app.route('/sse', methods=['GET'])
def sse():
    def generate():
        # Başlangıç mesajı
        yield f"data: {json.dumps({'type': 'connected', 'server': SERVER_INFO})}\n\n"
        
        # Keep-alive ping
        while True:
            time.sleep(30)
            yield ": ping\n\n"
    
    response = Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
            # CORS header'ları nginx tarafından ekleniyor
        }
    )
    return response


# Root endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "name": SERVER_INFO["name"],
        "version": SERVER_INFO["version"],
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
            "sse": "/sse"
        }
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"MCP HTTP Server running on port {port}")
    print(f"Server info: {json.dumps(SERVER_INFO, indent=2)}")
    app.run(host='0.0.0.0', port=port)
