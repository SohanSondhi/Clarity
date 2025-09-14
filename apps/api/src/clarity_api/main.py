from fastapi import FastAPI
from .app import app as _app

# Simple module entry point: `python -m clarity_api.main`
app: FastAPI = _app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)


