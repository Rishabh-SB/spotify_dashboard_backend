from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import upload, metrics

app = FastAPI(title="Spotify Dashboard Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # For development, allow all origins. For production, specify frontend URLs.
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])


@app.get("/")
async def root():
    return {"message": "Spotify Dashboard Backend is alive!"}
