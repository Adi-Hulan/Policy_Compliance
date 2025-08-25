import { cn } from '@/lib/utils'
import { ChatMessageItem } from '@/components/chat-message'
import { useChatScroll } from '@/hooks/use-chat-scroll'
import { useRealtimeChat } from '@/hooks/use-realtime-chat';
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Send } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'


/**
 * Realtime chat component
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

  useEffect(() => {
    if (onMessage) {
      onMessage(allMessages)
    }
  }, [allMessages, onMessage])

  useEffect(() => {
    // Scroll to bottom whenever messages change
    scrollToBottom()
  }, [allMessages, scrollToBottom])

  const handleSendMessage = useCallback((e) => {
    e.preventDefault()
    if (!newMessage.trim() || !isConnected) return

    sendMessage(newMessage)
    setNewMessage('')
  }, [newMessage, isConnected, sendMessage])

  return (
    <div
      className="flex flex-col h-full w-full bg-background text-foreground antialiased">
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
        <Input
          className={cn(
            'rounded-full bg-background text-sm transition-all duration-300',
            isConnected && newMessage.trim() ? 'w-[calc(100%-36px)]' : 'w-full'
          )}
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
          disabled={!isConnected} />
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
