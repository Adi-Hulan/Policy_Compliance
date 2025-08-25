'use client';
import { useCallback, useEffect, useState } from 'react'
import supabase from '@/lib/supabase/client'

const EVENT_MESSAGE_TYPE = 'message'

export function useRealtimeChat({
  roomName,
  username
}) {
  const [messages, setMessages] = useState([])
  const [channel, setChannel] = useState(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    const newChannel = supabase.channel(roomName)

    newChannel
      .on('broadcast', { event: EVENT_MESSAGE_TYPE }, (payload) => {
        setMessages((current) => [...current, payload.payload])
      })
      .subscribe(async (status) => {
        if (status === 'SUBSCRIBED') {
          setIsConnected(true)
        }
      })

    setChannel(newChannel)

    return () => {
      supabase.removeChannel(newChannel)
    };
  }, [roomName, username, supabase])

  const sendMessage = useCallback(async (content) => {
    if (!channel || !isConnected) return

    const message = {
      id: crypto.randomUUID(),
      content,
      user: {
        name: username,
      },
      createdAt: new Date().toISOString(),
      room: roomName ?? 'my-chat-room',
    }

    // Update local state immediately for the sender
    setMessages((current) => [...current, message])

    // Send message to realtime channel
    await channel.send({
      type: 'broadcast',
      event: EVENT_MESSAGE_TYPE,
      payload: message,
    })

    // Send message to backend for analysis
    try {
      const response = await fetch('http://127.0.0.1:5000/queries/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: content }),
      })
      
      if (!response.ok) {
        console.error('Failed to analyze message:', await response.text())
      }
    } catch (error) {
      console.error('Error sending message for analysis:', error)
    }
  }, [channel, isConnected, username])

  return { messages, sendMessage, isConnected }
}
