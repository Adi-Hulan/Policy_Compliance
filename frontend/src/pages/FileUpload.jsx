// FileUpload.js
import React, { useState } from "react";
import supabase from '@/lib/supabase/client';

export default function FileUpload() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [fileUrl, setFileUrl] = useState("");

  // Handle file selection
  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file first!");
      return;
    }

    // Get the current authenticated user
    const { data: sessionData } = await supabase.auth.getSession();
    const user = sessionData?.session?.user;

    if (!user) {
      setMessage("You must be logged in to upload files.");
      return;
    }

    try {
      // Upload file to Supabase storage under user-specific folder
      const { data, error } = await supabase.storage
        .from("documents") // your bucket name
        .upload(`uploads/${user.id}/${file.name}`, file, {
          cacheControl: "3600",
          upsert: false,
          metadata: { owner: user.id }, // for RLS
        });

      if (error) throw error;

      // Get public URL (optional, if your bucket allows)
      const { data: publicUrlData } = supabase.storage
        .from("documents")
        .getPublicUrl(`uploads/${user.id}/${file.name}`);

      setFileUrl(publicUrlData.publicUrl);
      setMessage("File uploaded successfully!");
    } catch (error) {
      console.error("Upload error:", error);
      setMessage(`Upload failed: ${error.message}`);
    }
  };

  return (
    <div style={{ maxWidth: "400px", margin: "auto", textAlign: "center" }}>
      <h2>Upload File</h2>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} style={{ marginTop: "10px" }}>
        Upload
      </button>
      {message && <p>{message}</p>}
      {fileUrl && (
        <p>
          File URL: <a href={fileUrl} target="_blank" rel="noopener noreferrer">{fileUrl}</a>
        </p>
      )}
    </div>
  );
}
