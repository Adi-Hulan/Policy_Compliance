import supabase from "@/lib/supabase/client";

export async function storeMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0) return;

  // Map incoming messages to your table schema
  const formatted = messages.map((msg) => ({
    id: msg.id,
    content: msg.content,
    // DB column is `username` (string) — write that so Supabase accepts the insert
    username: msg.user?.name ?? msg.username ?? null,
    created_at: msg.createdAt,
    room: msg.room || null, // include room if needed
  }));

  console.log("Inserting rows:", formatted);
  // Use upsert with onConflict on the primary key (id) so repeated attempts
  // to store the same message (same `id`) are idempotent and won't fail
  // with a duplicate key error. This handles cases where multiple clients
  // receive a broadcast and all try to persist the same message.
  // If your DB generates ids server-side (non-UUID), adapt to a different
  // reconciliation strategy instead of relying on client-provided ids.
  const { data, error } = await supabase
    .from("messages")
    .upsert(formatted, { onConflict: "id" })
    .select();

  console.log("Insert result:", { data, error });

  if (error) {
    console.error("Error inserting messages:", error);
    throw error;
  }

  return data;
}
