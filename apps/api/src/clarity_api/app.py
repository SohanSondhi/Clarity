from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .routes.tree import router as tree_router
from .routes.rename import router as rename_router
from .routes.refresh import router as refresh_router
from .routes.delete import router as delete_router
from .routes.create import router as create_router
from .routes.index import router as index_router
from .routes.clear import router as clear_router

app = FastAPI(
    title="Clarity API",
    description="API for Clarity search and indexing system",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tree_router, tags=["tree"])
app.include_router(rename_router, tags=["rename"])
app.include_router(refresh_router, tags=["refresh"])
app.include_router(delete_router, tags=["delete"])
app.include_router(create_router, tags=["create"])
app.include_router(index_router, tags=["index"])
app.include_router(clear_router, tags=["clear"])

@app.get("/")
async def root():
    return {"message": "Clarity API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)