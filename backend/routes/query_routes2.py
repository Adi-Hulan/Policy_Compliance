"""
Query Routes Module

FastAPI routes for handling chat queries with streaming responses.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse
from orchestrator.orchestrator import get_orchestrator
from db.repositories.chat_repository import ChatRepository
from middleware.shared_auth import verify_jwt_token  # Use shared auth instead of Flask decorator
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

query_bp = APIRouter(prefix="/queries", tags=["queries"])  # FastAPI APIRouter instead of Flask Blueprint


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency to authenticate user via JWT using shared_auth.
    Extracts token from Authorization header, verifies it, and returns user data.
    Raises HTTPException on failure.
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    try:
        # Extract token from "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = parts[1]
        user_data = verify_jwt_token(token)  # Use shared function
        return user_data  # Dict with user_id, user_email, user_role
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@query_bp.post("/analyze/stream")
async def analyze_stream(
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user)  # Authentication enabled
):
    """
    Stream chat responses as Server-Sent Events (SSE).
    
    Request body:
        {
            "session_id": str,
            "message": str,
            "document_url": str (optional)
        }
    
    Returns:
        SSE stream with events:
        - stage: Progress updates
        - llm_stream: Streaming LLM tokens
        - llm_final: Final LLM response
        - final: Complete response
        - end: Stream completion
        - error: Error occurred
    """
    print("=" * 80)
    print("[ROUTE] /analyze/stream endpoint called")
    print(f"[ROUTE] User ID: {user['user_id']}")
    print(f"[ROUTE] User Email: {user['user_email']}")
    print("=" * 80)
    
    try:
        # Parse request body
        data = await request.json()
        session_id = data.get("session_id")
        message = data.get("message")
        document_url = data.get("document_url")
        
        # Validate required fields
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        if not message:
            raise HTTPException(status_code=400, detail="message is required")
        
        print(f"[ROUTE] Session: {session_id}")
        print(f"[ROUTE] Message: {message[:100]}...")
        if document_url:
            print(f"[ROUTE] Document URL: {document_url}")
        
        # Validate session ownership
        repo = ChatRepository()
        user_id = user['user_id']  # Use authenticated user ID
        existing_session = repo.get_session(session_id)
        
        if existing_session and existing_session.get('user_id') != user_id:
            print(f"[ROUTE] ✗ Forbidden: session belongs to different user")
            raise HTTPException(status_code=403, detail="Forbidden: session does not belong to user")
        
        print(f"[ROUTE] ✓ Session ownership validated")
        
        print(f"[ROUTE] ✓ Session ownership validated")
        
        # Get orchestrator and create stream generator
        print(f"[ROUTE] Getting orchestrator...")
        orchestrator = get_orchestrator()
        
        print(f"[ROUTE] Creating stream generator...")
        stream_generator = orchestrator.create_stream_generator(
            session_id=session_id,
            message=message,
            document_url=document_url,
            user_id=user_id
        )
        
        print(f"[ROUTE] ✓ Stream generator created, returning SSE response")
        print("=" * 80)
        
        # Return SSE response (async generator assumed compatible)
        return StreamingResponse(
            stream_generator,
            media_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',  # Disable nginx buffering
            }
        )

    except KeyError as e:
        print(f"[ROUTE] ✗ Missing required field: {e}")
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")
        
    except Exception as e:
        print(f"[ROUTE] ✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))