import React, { useState, useEffect } from "react";
import supabase from '@/lib/supabase/client';
import { getToken } from '@/lib/auth';

const ChatSystem = () => {
  const [chats, setChats] = useState([]);
  const [currentChat, setCurrentChat] = useState(null);
  const [message, setMessage] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [showFileInput, setShowFileInput] = useState(false);

  // Fetch user's chats
  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    const { data: chats } = await supabase
      .from('chats')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });
    setChats(chats || []);
  };

  const createNewChat = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    const { data: chat } = await supabase
      .from('chats')
      .insert([{ user_id: user.id, title: 'New Chat' }])
      .select()
      .single();
    
    setChats([chat, ...chats]);
    setCurrentChat(chat);
    setMessages([]);
  };

  const fetchMessages = async (chatId) => {
    const { data: messages } = await supabase
      .from('chat_messages')
      .select('*')
      .eq('chat_id', chatId)
      .order('created_at', { ascending: true });
    setMessages(messages || []);
  };

  const handleFileUpload = async (file) => {
    const fileName = `${Date.now()}-${file.name}`;
    const { data, error } = await supabase.storage
      .from("documents")
      .upload(fileName, file);

    if (error) throw error;

    const { data: publicUrlData } = supabase.storage
      .from("documents")
      .getPublicUrl(fileName);

    await supabase.from('chat_documents').insert([{
      chat_id: currentChat.id,
      file_name: file.name,
      file_url: publicUrlData.publicUrl,
      file_type: file.type,
      file_size: file.size
    }]);

    return publicUrlData.publicUrl;
  };

  const sendMessage = async () => {
    if (!message.trim() && !file) return;

    setLoading(true);
    try {
      let fileUrl = null;
      let messageContent = message;

      // Only handle file if one is attached
      if (file) {
        fileUrl = await handleFileUpload(file);
        // Add file information to message content
        messageContent += `\n[Attached file: ${file.name}]`;
      }

      // Store user message
      const { data: userMessage } = await supabase
        .from('chat_messages')
        .insert([{
          chat_id: currentChat.id,
          content: messageContent,
          role: 'user'
        }])
        .select()
        .single();

      // Update messages immediately for better UX
      setMessages(prev => [...prev, userMessage]);

      // Get chat history
      const { data: chatHistory } = await supabase
        .from('chat_messages')
        .select('*')
        .eq('chat_id', currentChat.id)
        .order('created_at', { ascending: true });

      // Send to backend API with context
      const response = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${await getToken()}`,
        },
        body: JSON.stringify({
          message: messageContent,
          fileUrl,
          chatHistory,
          chatId: currentChat.id
        }),
      });

      const result = await response.json();

      // Store assistant response
      await supabase.from('chat_messages').insert([{
        chat_id: currentChat.id,
        content: result.response,
        role: 'assistant'
      }]);

      // Refresh messages
      await fetchMessages(currentChat.id);

      // Clear inputs
      setMessage("");
      setFile(null);
      setShowFileInput(false);
    } catch (err) {
      console.error(err);
      alert("Something went wrong!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-gray-100 p-4">
        <button
          onClick={createNewChat}
          className="w-full bg-blue-500 text-white p-2 rounded mb-4"
        >
          New Chat
        </button>
        <div className="space-y-2">
          {chats.map((chat) => (
            <div
              key={chat.id}
              onClick={() => {
                setCurrentChat(chat);
                fetchMessages(chat.id);
              }}
              className={`p-2 rounded cursor-pointer ${
                currentChat?.id === chat.id ? 'bg-blue-100' : 'hover:bg-gray-200'
              }`}
            >
              {chat.title}
            </div>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentChat ? (
          <>
            {/* Messages */}
            <div className="flex-1 p-4 overflow-auto">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`mb-4 p-3 rounded ${
                    msg.role === 'user' ? 'bg-blue-100 ml-auto' : 'bg-gray-100'
                  }`}
                  style={{ maxWidth: '80%' }}
                >
                  {msg.content}
                </div>
              ))}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t">
              <div className="flex items-center mb-2">
                <button
                  type="button"
                  onClick={() => setShowFileInput(!showFileInput)}
                  className="text-blue-500 hover:text-blue-700 flex items-center"
                >
                  <svg 
                    className="w-5 h-5 mr-1" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path 
                      strokeLinecap="round" 
                      strokeLinejoin="round" 
                      strokeWidth={2} 
                      d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" 
                    />
                  </svg>
                  {showFileInput ? 'Hide attachment' : 'Attach file'}
                </button>
              </div>
              
              {showFileInput && (
                <div className="mb-2">
                  <input
                    type="file"
                    onChange={(e) => setFile(e.target.files[0])}
                    className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-md file:border-0
                      file:text-sm file:font-semibold
                      file:bg-blue-50 file:text-blue-700
                      hover:file:bg-blue-100"
                  />
                  {file && (
                    <div className="mt-1 text-sm text-gray-500 flex items-center">
                      <span className="truncate">{file.name}</span>
                      <button
                        onClick={() => setFile(null)}
                        className="ml-2 text-red-500 hover:text-red-700"
                      >
                        ×
                      </button>
                    </div>
                  )}
                </div>
              )}

              <div className="flex">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  className="flex-1 p-2 border rounded-l"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || (!message.trim() && !file)}
                  className={`px-4 py-2 rounded-r ${
                    loading || (!message.trim() && !file)
                      ? 'bg-blue-300 cursor-not-allowed'
                      : 'bg-blue-500 hover:bg-blue-600'
                  } text-white`}
                >
                  {loading ? "Sending..." : "Send"}
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-gray-500">Select or create a chat to begin</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatSystem;