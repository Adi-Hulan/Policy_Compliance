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

  console.log('Inserting rows:', formatted)
  // request the inserted rows to be returned
  const { data, error } = await supabase.from("messages").insert(formatted).select();

  console.log("Insert result:", { data, error });

  if (error) {
    console.error("Error inserting messages:", error);
    throw error;
  }

  return data;
}
