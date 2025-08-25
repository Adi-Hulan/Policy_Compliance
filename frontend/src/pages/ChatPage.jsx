import React from 'react';
import { RealtimeChat } from '@/components/realtime-chat';
import { useMessagesQuery } from '@/hooks/useMessagesQuery';
import { storeMessages } from '@/lib/store-messages';

export default function ChatPage() {
  const { data: messages, loading, error } = useMessagesQuery('my-chat-room');

  const handleMessage = async (newMessages) => {
    try {
      await storeMessages(newMessages);
    } catch (err) {
      console.error('Failed to store messages:', err);
    }
  };

  if (loading) return <div>Loading messages...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <RealtimeChat
      roomName="my-chat-room"
      username="john_doe"
      messages={messages}
      onMessage={handleMessage}
    />
  );
}
