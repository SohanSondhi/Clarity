from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from .routes.directory import router as directory_router
from .routes.search import router as search_router

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
app.include_router(directory_router, tags=["directory"])
app.include_router(search_router, tags=["search"])

@app.get("/")
async def root():
    return {"message": "Clarity API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)