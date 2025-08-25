import supabase from '@/lib/supabase/client';

export async function storeMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0) return;

  // Map incoming messages to your table schema
  const formatted = messages.map(msg => ({
    id: msg.id,
    content: msg.content,
    user_name: msg.user?.name,
    created_at: msg.createdAt,
    room: msg.room || null, // include room if needed
  }));

  const { data, error } = await supabase
    .from('messages')
    .insert(formatted);

    console.log('Insert result:', { data, error });

  if (error) {
    console.error('Error inserting messages:', error);
    throw error;
  }

  return data;
}
