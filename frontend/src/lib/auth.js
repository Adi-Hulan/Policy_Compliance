// src/lib/auth.js
import supabase from "@/lib/supabase/client";

export async function getToken() {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token || null;
}
