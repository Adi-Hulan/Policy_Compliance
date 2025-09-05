import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { PaperclipIcon, XIcon } from 'lucide-react';
import supabase from '@/lib/supabase/client';
import { getToken } from '@/lib/auth';

export function FileUploader({ onFileUpload, onClearFile }) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);
  
  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    setIsUploading(true);
    setUploadError(null);
    
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
      
      // Following the logic from DocAttach.jsx
      const fileName = `${Date.now()}-${file.name}`;
      
      // Upload file to Supabase storage
      const { data, error } = await supabase.storage
        .from("documents") // your bucket name
        .upload(fileName, file);
        
      if (error) {
        console.error("Supabase storage error:", error);
        throw error;
      }
      
      // Get public URL
      const { data: publicUrlData } = supabase.storage
        .from("documents")
        .getPublicUrl(fileName);
      
      const fileUrl = publicUrlData.publicUrl;
      
      console.log("File uploaded to:", fileUrl);
      
      // Prepare metadata following DocAttach.jsx format
      const metadata = {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        fileUrl: fileUrl,
      };
      
      // Call the onFileUpload callback with file details in the expected format
      onFileUpload({
        metadata,
        fileUrl
      });
      
    } catch (error) {
      console.error("File upload error:", error);
      
      // More helpful error message for RLS policy violations and other common errors
      if (error.message?.includes("row-level security policy")) {
        setUploadError("Permission denied. Authentication required for uploads.");
      } else if (error.message?.includes("Authentication required")) {
        setUploadError("Authentication required for uploads.");
      } else if (error.message?.includes("column")) {
        setUploadError("Database schema error. Please contact support.");
      } else if (error.message?.includes("not found")) {
        setUploadError("Storage bucket not found. Please check configuration.");
      } else {
        setUploadError(error.message || "Unknown upload error");
      }
    } finally {
      setIsUploading(false);
    }
  };
  
  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };
  
  return (
    <div className="flex items-center">
      <input 
        type="file" 
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".pdf,.doc,.docx,.txt"
      />
      
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={triggerFileInput}
        disabled={isUploading}
        title="Attach document"
        className="rounded-full h-9 w-9"
      >
        <PaperclipIcon className="h-5 w-5" />
      </Button>
      
      {uploadError && (
        <div className="text-xs text-red-500 ml-2">{uploadError}</div>
      )}
    </div>
  );
}
