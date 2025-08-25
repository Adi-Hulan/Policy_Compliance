import { useState, useEffect } from "react";
import supabase from "@/lib/supabase/client";

// fetch chat messages from your Supabase messages table
// for a given roomName and expose them to your React components.
export function useMessagesQuery(roomName) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchMessages() {
      const { data, error } = await supabase
        .from("messages")
        .select("*")
        .eq("room", roomName)
        .order("created_at", { ascending: true });

      if (error) {
        setError(error);
      } else {
        // Map DB rows to the frontend message shape { id, content, user: { name }, createdAt, room }
        const mapped = (data || []).map((row) => ({
          id: row.id,
          content: row.content,
          user: { name: row.username ?? null },
          createdAt: row.created_at
            ? new Date(row.created_at).toISOString()
            : null,
          room: row.room ?? null,
        }));
        setMessages(mapped);
      }
      setLoading(false);
    }

    fetchMessages();
  }, [roomName]);

  return { data: messages, loading, error };
}
