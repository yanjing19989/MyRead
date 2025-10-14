# GitHub Copilot Instructions for MyRead

## Project Overview

MyRead is a high-performance local photo album browser designed for managing and viewing large image collections (ZIP archives or folders). It supports 100+ albums with ~1000 images each, with direct ZIP reading without extraction.

## Technology Stack

### Backend
- **Python 3.11+** with modern Python features
- **FastAPI** - High-performance async web framework
- **Uvicorn** - ASGI server
- **SQLite (WAL mode)** - Lightweight database with concurrent read support
- **Pillow** - Image processing (WebP, EXIF orientation correction)
- **aiosqlite** - Async SQLite driver
- **natsort** - Natural sorting support

### Frontend
- **Native HTML/CSS/JavaScript** - No framework dependencies
- **Virtual lists** - Efficient rendering for large image sets
- **SSE (Server-Sent Events)** - Real-time scan progress updates

## Architecture

- **Async-first**: All I/O operations use async/await patterns
- **Caching**: Smart thumbnail caching with LRU strategy
- **Stream-based**: ZIP files are read via streaming without full extraction
- **Concurrent**: Configurable I/O and decode concurrency

## Code Standards

### Python Style
- Follow **PEP 8** strictly
- Use **type hints** for all function parameters and return values
- Use `async/await` for all asynchronous functions
- Import pattern: `from __future__ import annotations` for forward references
- Use Pydantic models for configuration and data validation

### Naming Conventions
- Python: `snake_case` for variables, functions, and files
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- API endpoints: camelCase in JSON responses, snake_case internally

### Database
- SQLite with WAL mode enabled
- Foreign keys must be enabled (`PRAGMA foreign_keys=ON`)
- Schema changes require careful consideration for backward compatibility
- Use aiosqlite for all database operations
- Always use connection pooling via `get_db()` dependency

### File Structure
```
app/
├── main.py           # FastAPI app entry point
├── db.py             # Database initialization and connection
├── settings.py       # Configuration management
├── routers/          # API route handlers
├── services/         # Business logic
└── utils/            # Utility functions
```

## Environment Configuration

Configuration via environment variables (see `app/settings.py`):
- `APP_CACHE_DIR` - Cache directory path
- `APP_CACHE_MAX_BYTES` - Cache size limit (default: 10GB)
- `APP_DEFAULT_QUALITY` - Image quality (1-100, default: 75)
- `APP_ENCODE_FORMAT` - Output format (webp/jpeg/png)
- `APP_IO_CONCURRENCY` - I/O concurrency (default: 8)
- `APP_DECODE_CONCURRENCY` - Decode concurrency (default: 3)
- `APP_ALLOW_RECURSIVE` - Enable recursive scanning
- `APP_MAX_INPUT_PIXELS` - Max input pixels (default: 178MP)

## Development Workflow

### Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Running
```bash
python server.py  # Development mode with auto-reload
# Or: uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### API Documentation
Access FastAPI auto-generated docs at `http://127.0.0.1:8000/docs`

## Security Considerations

- **Local only**: Server binds to 127.0.0.1 only
- **No authentication**: Single-user design, not for multi-user or public deployment
- **File access**: Backend can access all files in configured paths - be careful with permissions

## Common Patterns

### Async Route Handler
```python
from fastapi import APIRouter, Depends
import aiosqlite
from app.db import get_db

router = APIRouter()

@router.get("/endpoint")
async def handler(db: aiosqlite.Connection = Depends(get_db)):
    async with db.execute("SELECT ...") as cur:
        rows = await cur.fetchall()
    return {"data": rows}
```

### Settings Access
```python
from app.routers.settings import runtime_settings

# Access current runtime settings
cache_dir = runtime_settings.cache_dir
quality = runtime_settings.default_quality
```

### Error Handling
- Use FastAPI's HTTPException for API errors
- Log errors appropriately
- Return meaningful error messages to the frontend

## Testing

Currently, there is no automated test infrastructure. Testing is done through:
1. Running the development server
2. Manual testing via the web UI
3. Testing API endpoints via `/docs`

## Troubleshooting Tips

### Common Issues
- **Thumbnails not showing**: Check `cache/thumbs/` permissions
- **Scan failures**: Verify path exists and has read permissions
- **Performance issues**: Adjust `APP_IO_CONCURRENCY` and `APP_DECODE_CONCURRENCY`
- **Port conflicts**: Modify port in `server.py`

## Best Practices for Changes

1. **Minimal changes**: Make the smallest possible modifications
2. **Type safety**: Always use type hints
3. **Async patterns**: Keep async/await usage consistent
4. **Database transactions**: Always commit changes
5. **Resource cleanup**: Ensure connections and file handles are properly closed
6. **Error handling**: Gracefully handle all error cases
7. **Documentation**: Update README.md if adding features or changing behavior

## Language Note

Primary documentation and UI are in Chinese, but code comments and commit messages can be in English.
