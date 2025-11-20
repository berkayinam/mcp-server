# Simple HTTP MCP Server

Basit bir HTTP modlu MCP (Model Context Protocol) server'ı. mcp-use ve MCP Inspector ile uyumludur.

## Özellikler

- HTTP modlu MCP server
- mcp-use uyumlu
- MCP Inspector uyumlu
- CORS desteği
- Basit tool'lar: echo, add, get_time

## Endpoint'ler

- `POST /mcp` - MCP mesajlarını handle eder
- `GET /sse` - Server-sent events (inspector için)
- `GET /health` - Health check
- `GET /` - Server bilgileri

## Docker ile Çalıştırma

```bash
# Build
docker build -t mcp-http-server .

# Run
docker run -p 8080:8080 mcp-http-server
```

## Yerel Çalıştırma

```bash
pip install -r requirements.txt
python server.py
```

Server `http://localhost:8080` adresinde çalışacaktır.

## MCP Tool'ları

1. **echo** - Girdi metnini geri döndürür
2. **add** - İki sayıyı toplar
3. **get_time** - Mevcut zamanı döndürür
