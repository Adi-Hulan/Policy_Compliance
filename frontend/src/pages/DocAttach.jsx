import React, { useState } from "react";
import supabase from '@/lib/supabase/client';
import { getToken } from '@/lib/auth';

const FileUploadForm = () => {
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !text) {
      alert("Please select a file and enter text");
      return;
    }

    setLoading(true);

    try {
      // Make sure user is signed in to Supabase for storage access
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        console.log("No active session, signing in anonymously");
        // Try anonymous sign-in
        const { error: signInError } = await supabase.auth.signInAnonymously();
        if (signInError) {
          console.error("Anonymous sign-in failed:", signInError);
          throw new Error('Authentication required for file uploads');
        }
        console.log("Anonymous sign-in successful");
      }
      
      // 1. Upload file to Supabase storage
      const fileName = `${Date.now()}-${file.name}`;
      const { data, error } = await supabase.storage
        .from("documents") // your Supabase bucket name
        .upload(fileName, file);

      if (error) {
        console.error("Supabase storage error:", error);
        throw error;
      }

      // 2. Get public URL of uploaded file
      const { data: publicUrlData } = supabase.storage
        .from("documents")
        .getPublicUrl(fileName);

      const fileUrl = publicUrlData.publicUrl;

      // 3. Prepare metadata
      const metadata = {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        fileUrl: fileUrl,
      };

      console.log("Temp File uploaded to:", fileUrl);
      
      // 4. Send text + metadata to backend API
      const response = await fetch("http://127.0.0.1:5000/documents/upload/temp", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${await getToken()}`,
        },
        body: JSON.stringify({
          query: text,
          metadata,
          fileUrl
        }),
      });

      const result = await response.json();
      console.log("Backend response:", result);
      setResponse(result);

      alert("File and text submitted successfully!");
      setText("");
      setFile(null);
    } catch (err) {
      console.error(err);
      alert("Something went wrong!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border rounded-md">
      <input type="file" onChange={handleFileChange} />
      <br />
      <input
        type="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter your text"
        className="border p-2 mt-2 w-full"
      />
      <br />
      <button
        type="submit"
        disabled={loading}
        className="mt-3 bg-blue-500 text-white px-4 py-2 rounded"
      >
        {loading ? "Uploading..." : "Submit"}
      </button>
      
      {response && (
        <div className="mt-4 p-4 bg-gray-100 rounded-md">
          <h3 className="font-semibold mb-2">Response from Analysis:</h3>
          <p className="whitespace-pre-wrap">{response.result}</p>
        </div>
      )}
    </form>
  );
};

export default FileUploadForm;
