"use client";
import { useCallback, useEffect, useState } from "react";
import supabase from "@/lib/supabase/client";

const EVENT_MESSAGE_TYPE = "message";

export function useRealtimeChat({ roomName, username }) {
  const [messages, setMessages] = useState([]);
  const [channel, setChannel] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // Subscribe to Postgres inserts on the `messages` table. This subscription
  // is the single source of truth for persisted messages. Incoming INSERT
  // events from Postgres will be reconciled against any optimistic messages
  // the client created earlier.
  useEffect(() => {
    const dbChannel = supabase.channel("messages-db");

    // INSERT handler: add or replace optimistic message
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

    // UPDATE handler: replace existing message with updated persisted row
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
          // If we didn't have it locally, append the updated row so UI stays
          // consistent with DB.
          return [...current, mapped];
        });
      }
    );

    // DELETE handler: remove the message from local state
    dbChannel.on(
      "postgres_changes",
      { event: "DELETE", schema: "public", table: "messages" },
      (payload) => {
        const old = payload.old;
        if (!old) return;
        setMessages((current) => current.filter((m) => m.id !== old.id));
      }
    );

    // subscribe and reflect connection state
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

  // sendMessage now inserts directly into the Supabase `messages` table.
  // We implement optimistic UI by adding a local message with `_status: 'sending'`
  // and a client-generated id. When the DB insert is confirmed (either via
  // the immediate insert response or via the Postgres subscription), we
  // reconcile and replace the optimistic message with the persisted row.
  // If insertion fails we remove the optimistic message and surface an error.
  const sendMessage = useCallback(
    async (content) => {
      if (!isConnected) {
        console.log("[realtime] sendMessage aborted - not connected");
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

      // Add optimistic message immediately so UI feels responsive
      setMessages((current) => [...current, optimistic]);

      try {
        // Attempt to insert into the DB. We include the client-generated id so
        // the inserted row will have the same id; this makes reconciliation
        // simple when the Postgres subscription delivers the INSERT event.
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

        // If insert returns the persisted row, replace optimistic entry with it.
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
        console.error("Failed to insert message:", err);

        // Remove optimistic message and let UI surface an error (toast or similar)
        setMessages((current) => current.filter((m) => m.id !== clientId));
        // Small, framework-agnostic error surface: replace with your app's toast
        // system (e.g. react-hot-toast, shadcn toast, etc.) in a real app.
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
