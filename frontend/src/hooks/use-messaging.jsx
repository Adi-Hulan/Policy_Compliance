"use client";
import { useCallback, useEffect, useState } from "react";
import supabase from "@/lib/supabase/client";

const BACKEND_API_URL = "http://localhost:5000/api";

export function useMessaging({ roomName, username }) {
  const [messages, setMessages] = useState([]);
  const [channel, setChannel] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // Subscribe to Postgres changes for real-time updates
  useEffect(() => {
    const dbChannel = supabase.channel("messages-db");

    // Listen for INSERT events to show new messages in real-time
    dbChannel.on(
      "postgres_changes",
      { event: "INSERT", schema: "public", table: "messages" },
      (payload) => {
        const row = payload.new;
        const mapped = {
          id: row.id,
          content: row.content,
          user: { name: row.username ?? null },
          createdAt: row.created_at ? new Date(row.created_at).toISOString() : null,
          room: row.room ?? null,
        };

        setMessages((current) => {
          const existing = current.find((m) => m.id === mapped.id);
          if (existing) {
            if (existing._status === "sending") {
              return current.map((m) => (m.id === mapped.id ? mapped : m));
            }
            return current;
          }
          return [...current, mapped];
        });
      }
    );

    // Listen for UPDATE and DELETE events
    dbChannel.on(
      "postgres_changes",
      { event: "UPDATE", schema: "public", table: "messages" },
      (payload) => {
        const row = payload.new;
        const mapped = {
          id: row.id,
          content: row.content,
          user: { name: row.username ?? null },
          createdAt: row.created_at ? new Date(row.created_at).toISOString() : null,
          room: row.room ?? null,
        };

        setMessages((current) => {
          const found = current.find((m) => m.id === mapped.id);
          if (found) {
            return current.map((m) => (m.id === mapped.id ? mapped : m));
          }
          return [...current, mapped];
        });
      }
    );

    dbChannel.on(
      "postgres_changes",
      { event: "DELETE", schema: "public", table: "messages" },
      (payload) => {
        const old = payload.old;
        if (!old) return;
        setMessages((current) => current.filter((m) => m.id !== old.id));
      }
    );

    // Subscribe and handle connection state
    dbChannel.subscribe((status) => {
      if (status === "SUBSCRIBED") setIsConnected(true);
      if (status === "CLOSED" || status === "UNSUBSCRIBED") setIsConnected(false);
    });

    setChannel(dbChannel);

    // Cleanup subscription on unmount
    return () => {
      supabase.removeChannel(dbChannel);
    };
  }, [roomName, username]);

  // Send message function with Supabase insert + REST API call
  const sendMessage = useCallback(
    async (content) => {
      if (!isConnected) {
        console.log("[messaging] sendMessage aborted - not connected");
        return;
      }

      const clientId = crypto.randomUUID();

      const optimistic = {
        id: clientId,
        content,
        user: { name: username },
        createdAt: new Date().toISOString(),
        room: roomName ?? "my-chat-room",
        _status: "sending",
      };

      // Add optimistic message immediately for responsive UI
      setMessages((current) => [...current, optimistic]);

      try {
        // Step 1: Insert message into Supabase
        console.log("[messaging] Inserting message into Supabase...");
        const { data, error } = await supabase
          .from("messages")
          .insert([
            {
              id: clientId,
              content,
              username: username,
              room: roomName ?? "my-chat-room",
              created_at: new Date().toISOString(),
            },
          ])
          .select()
          .single();

        if (error) throw error;

        console.log("[messaging] ✅ Message inserted into Supabase:", data.id);

        // Step 2: Send message to Flask backend via REST API
        console.log("[messaging] Sending message to Flask backend...");
        
        const backendPayload = {
          id: data.id,
          username: data.username,
          content: data.content,
          room: data.room,
          created_at: data.created_at,
        };

        const response = await fetch(`${BACKEND_API_URL}/messages`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(backendPayload),
        });

        const result = await response.json();

        if (!response.ok) {
          console.error("[messaging] Backend processing failed:", result);
          // Don't throw error here - message is already in Supabase
          // Just log the backend processing failure
        } else {
          console.log("[messaging] ✅ Message processed by backend:", result);
        }

        // Replace optimistic message with persisted data
        if (data) {
          const mapped = {
            id: data.id,
            content: data.content,
            user: { name: data.username ?? null },
            createdAt: data.created_at ? new Date(data.created_at).toISOString() : null,
            room: data.room ?? null,
          };

          setMessages((current) => current.map((m) => (m.id === clientId ? mapped : m)));
        }

      } catch (err) {
        console.error("[messaging] Error in message flow:", err);

        // Remove optimistic message on error
        setMessages((current) => current.filter((m) => m.id !== clientId));
        
        // Show user-friendly error
        try {
          window.alert("Failed to send message. Please try again.");
        } catch (e) {
          // ignore UI alert failures in non-browser environments
        }
      }
    },
    [isConnected, username, roomName]
  );

  return { messages, sendMessage, isConnected };
}
