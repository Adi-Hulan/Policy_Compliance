import asyncio
from supabase_client import supabase

# Global list to store messages temporarily
new_messages = []

def handle(payload):
    print("Payload received from Supabase:", payload)
    new_messages.append(payload['new'])
    print("New message appended:", new_messages[-1])

async def listen_new_messages():
    print("Starting Supabase listener...")
    subscription = supabase.realtime.channel("messages").on("INSERT", handle).subscribe()
    print("Subscription created:", subscription)
    while True:
        await asyncio.sleep(1)


# Optionally, run this in a separate thread or async process
