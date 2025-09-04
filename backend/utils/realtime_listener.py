''' DEPRECATED - not in use'''

import os
import asyncio
from realtime import AsyncRealtimeClient

# Route messages directly to the QueryAnalyzer instead of the orchestrator.
from agents.query_analyzer import QueryAnalyzer
from agents.chuck_retriever import Retriever

# create instances
analyzer = QueryAnalyzer()
retriever = Retriever()


# create async client using Supabase realtime websocket endpoint (wss)
# Supabase realtime URL is typically '<SUPABASE_URL>/realtime/v1'
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url:
    raise RuntimeError("SUPABASE_URL is not set in environment")

realtime = AsyncRealtimeClient(
    url=f"{supabase_url.rstrip('/')}/realtime/v1",
    token=supabase_key,
)


async def _start_listener():
    # subscribe to public.messages
    channel = realtime.channel("realtime:public:messages")

    # register postgres changes handler for INSERT on messages
    def _on_new_message(payload):
        data = payload.get("new") or payload.get("record") or payload
        if not data:
            return
        # only handle messages created by users
        if data.get("role") == "user":
            # extract probable text field(s)
            text = (
                data.get("content")
                or data.get("text")
                or data.get("message")
                or data.get("body")
                or data.get("payload")
                or str(data)
            )

            # Call the analyzer synchronously here. The listener itself should be
            # the background task; this keeps the analyis logic synchronous so
            # it's not scheduled separately.
            try:
                _handle_message_sync(text)
            except Exception as e:
                print("Error processing message synchronously:", e)

    channel.on_postgres_changes("INSERT", _on_new_message, table="messages", schema="public")

    # subscribe (opens the socket and starts listening)
    await realtime.subscribe(channel)


def _handle_message_sync(text: str):
    """Synchronous handler that runs in a background thread.

    It retrieves relevant chunks and calls the QueryAnalyzer. Keeping this sync
    avoids touching the realtime asyncio internals while still allowing network
    I/O via the model client.
    """
    try:
        # Retriever returns a dict {status, chunks} or a list; handle both.
        retrieved = retriever.retrieve_chunks(text)
        if isinstance(retrieved, dict):
            chunks = retrieved.get("chunks") or []
        else:
            chunks = retrieved

        response = analyzer.process(text, chunks)
        print("QueryAnalyzer result:", response)
    except Exception as e:
        print("Error handling realtime message:", e)


def start():
    """Start the realtime listener (non-blocking helper)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # run the async starter in background
    loop.create_task(_start_listener())


if __name__ == "__main__":
    # quick manual run
    start()
    asyncio.get_event_loop().run_forever()
