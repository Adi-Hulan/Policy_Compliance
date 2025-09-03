import React from 'react';
import { RealtimeChat } from '@/components/realtime-chat';
import { useMessagesQuery } from '@/hooks/useMessagesQuery';

export default function ChatPage() {
  const { data: messages, loading, error } = useMessagesQuery('my-chat-room');


  if (loading) return <div>Loading messages...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <RealtimeChat
      roomName="my-chat-room"
      username="john_doe"
      messages={messages}
    />
  );
}
