'use client';
import { createClient } from '@/lib/supabase/client'
import { useCallback, useEffect, useState } from 'react'

const EVENT_MESSAGE_TYPE = 'message'

export function useRealtimeChat({
  roomName,
  username
}) {
  const supabase = createClient()
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
    }

    // Update local state immediately for the sender
    setMessages((current) => [...current, message])

    await channel.send({
      type: 'broadcast',
      event: EVENT_MESSAGE_TYPE,
      payload: message,
    })
  }, [channel, isConnected, username])

  return { messages, sendMessage, isConnected }
}
