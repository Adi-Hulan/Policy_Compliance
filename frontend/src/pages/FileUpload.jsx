// FileUpload.js
import React, { useState } from "react";
import { createClient } from "@supabase/supabase-js";


const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

export default function FileUpload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const uploadFile = async () => {
    if (!file) return;

    const { data, error } = await supabase.storage
      .from("documents") // your private bucket
      .upload(`uploads/${Date.now()}_${file.name}`, file);

    if (error) {
      setMessage(`Error: ${error.message}`);
    } else {
      setMessage("Upload success! Processing...");
      
      // ✅ Send file path (NOT public URL) to backend
      await fetch("http://localhost:8000/process-file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: data.path }),
      });
    }
  };

  return (
    <div>
      <p>test</p>
      <input type="file" onChange={handleFileChange} />
      <button onClick={uploadFile}>Upload</button>
      <p>{message}</p>
    </div>
  );
}
