import { useState, useEffect } from 'react';
import supabase from '@/lib/supabase/client';

export function useMessagesQuery(roomName) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchMessages() {
      const { data, error } = await supabase
        .from('messages')
        .select('*')
        .eq('room', roomName)
        .order('created_at', { ascending: true });

      if (error) {
        setError(error);
      } else {
        setMessages(data || []);
      }
      setLoading(false);
    }

    fetchMessages();
  }, [roomName]);

  return { data: messages, loading, error };
}
