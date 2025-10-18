from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.query_routes2 import query_bp
from routes.document_routes import router as document_router
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Policy Compliance API - Queries", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include query routes only
app.include_router(query_bp)
app.include_router(document_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
