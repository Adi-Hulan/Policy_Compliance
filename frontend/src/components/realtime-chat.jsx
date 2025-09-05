import { cn } from '@/lib/utils'
import { ChatMessageItem } from '@/components/chat-message'
import { useChatScroll } from '@/hooks/use-chat-scroll'
import { useRealtimeChat } from '@/hooks/use-realtime-chat';
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send, FileText, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { FileUploader } from '@/components/file-uploader'


/**
 * Realtime chat component with Supabase + REST API messaging flow
 * @param roomName - The name of the room to join. Each room is a unique chat.
 * @param username - The username of the user
 * @param onMessage - The callback function to handle the messages. Useful if you want to store the messages in a database.
 * @param messages - The messages to display in the chat. Useful if you want to display messages from a database.
 * @returns The chat component
 */

export const RealtimeChat = ({
  roomName,
  username,
  onMessage,
  messages: initialMessages = []
}) => {
  const { containerRef, scrollToBottom } = useChatScroll()
  const [attachedFile, setAttachedFile] = useState(null)

  const {
    messages: realtimeMessages,
    sendMessage,
    isConnected,
  } = useRealtimeChat({
    roomName,
    username,
  })
  const [newMessage, setNewMessage] = useState('')

  // Merge realtime messages with initial messages
  const allMessages = useMemo(() => {
    const mergedMessages = [...initialMessages, ...realtimeMessages].map((msg) => {
      // Normalize timestamp coming from different sources (supabase timestamptz may appear
      // as `created_at`, or as a string/number/Date). Produce an ISO string or null.
      const raw = msg?.createdAt ?? msg?.created_at ?? null
      let created = null

      if (raw != null) {
        if (typeof raw === 'string') {
          const d = new Date(raw)
          created = Number.isNaN(d.getTime()) ? null : d.toISOString()
        } else if (typeof raw === 'number') {
          const d = new Date(raw)
          created = Number.isNaN(d.getTime()) ? null : d.toISOString()
        } else if (raw instanceof Date) {
          created = raw.toISOString()
        }
      }

      return { ...msg, createdAt: created }
    })
    // Remove duplicates based on message id
    const uniqueMessages = mergedMessages.filter(
      (message, index, self) => index === self.findIndex((m) => m.id === message.id)
    )
    // Sort by creation date (defensive: handle missing or non-string createdAt)
    const sortedMessages = uniqueMessages.sort((a, b) => {
      const toKey = (val) => {
        if (val == null) return null
        if (typeof val === 'string') return val
        const d = new Date(val)
        return Number.isNaN(d.getTime()) ? null : d.toISOString()
      }

      const aKey = toKey(a?.createdAt)
      const bKey = toKey(b?.createdAt)

      if (aKey === bKey) return 0
      if (aKey === null) return 1 // push items without a valid date to the end
      if (bKey === null) return -1

      return aKey.localeCompare(bKey)
    })

    return sortedMessages
  }, [initialMessages, realtimeMessages])

  // Only notify parent about new realtime messages (avoid re-storing initialMessages on mount)
  useEffect(() => {
    if (!onMessage) return
    if (!Array.isArray(realtimeMessages) || realtimeMessages.length === 0) return

    onMessage(realtimeMessages)
  }, [realtimeMessages, onMessage])

  useEffect(() => {
    // Scroll to bottom whenever messages change
    scrollToBottom()
  }, [allMessages, scrollToBottom])

  const handleSendMessage = useCallback((e) => {
    e.preventDefault()
    if (!newMessage.trim() || !isConnected) return

    // Send both message and file if available
    sendMessage(newMessage, attachedFile)
    
    // Clear message and file after sending
    setNewMessage('')
    setAttachedFile(null)
  }, [newMessage, attachedFile, isConnected, sendMessage])
  
  const handleFileUpload = (fileData) => {
    setAttachedFile(fileData)
  }
  
  const clearAttachedFile = () => {
    setAttachedFile(null)
  }

  return (
    <div
      className="flex flex-col h-full w-full bg-background text-foreground antialiased">
      
      {/* Connection Status */}
      <div className="flex items-center justify-between p-3 border-b border-border bg-muted/30">
        <div className="flex items-center space-x-2 text-sm">
          <div className={cn(
            "w-2 h-2 rounded-full",
            isConnected ? "bg-green-500" : "bg-red-500"
          )}></div>
          <span className="text-muted-foreground">
            {isConnected ? "Connected to Supabase" : "Disconnected"}
          </span>
        </div>
        <div className="text-xs text-muted-foreground">
          Room: {roomName} | User: {username}
        </div>
      </div>

      {/* Messages */}
      <div ref={containerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {allMessages.length === 0 ? (
          <div className="text-center text-sm text-muted-foreground">
            No messages yet. Start the conversation!
          </div>
        ) : null}
        <div className="space-y-1">
          {allMessages.map((message, index) => {
            const prevMessage = index > 0 ? allMessages[index - 1] : null
            const prevUserName = prevMessage?.user?.name ?? ''
            const messageUserName = message?.user?.name ?? ''
            const showHeader = !prevMessage || prevUserName !== messageUserName

            return (
              <div
                key={message.id}
                className="animate-in fade-in slide-in-from-bottom-4 duration-300">
                <ChatMessageItem
                  message={message}
                  isOwnMessage={messageUserName === username}
                  showHeader={showHeader} />
              </div>
            )
          })}
        </div>
      </div>
      <form
        onSubmit={handleSendMessage}
        className="flex w-full gap-2 border-t border-border p-4">
        
        {/* File attachment display */}
        {attachedFile && (
          <div className="absolute bottom-16 left-4 right-4 bg-muted/80 p-2 rounded-md flex items-center justify-between">
            <div className="flex items-center">
              <FileText className="h-4 w-4 mr-2 text-primary" />
              <span className="text-xs truncate max-w-[200px]">{attachedFile.metadata.fileName}</span>
            </div>
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-6 w-6 rounded-full"
              onClick={clearAttachedFile}
            >
              <X className="h-3 w-3" />
            </Button>
          </div>
        )}
        
        {/* File uploader */}
        <FileUploader 
          onFileUpload={handleFileUpload} 
          onClearFile={clearAttachedFile}
        />
        
        {/* Message input */}
        <Input
          className={cn(
            'rounded-full bg-background text-sm transition-all duration-300',
            isConnected && newMessage.trim() ? 'w-[calc(100%-80px)]' : 'w-[calc(100%-44px)]'
          )}
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder={attachedFile ? "Ask about this document..." : "Type a message..."}
          disabled={!isConnected} />
          
        {/* Send button */}
        {isConnected && newMessage.trim() && (
          <Button
            className="aspect-square rounded-full animate-in fade-in slide-in-from-right-4 duration-300"
            type="submit"
            disabled={!isConnected}>
            <Send className="size-4" />
          </Button>
        )}
      </form>
    </div>
  );
}
