import { cn } from '@/lib/utils'
import { FileText, ExternalLink } from 'lucide-react'

export const ChatMessageItem = ({
  message,
  isOwnMessage,
  showHeader
}) => {
  const userName = message?.user?.name ?? ''
  const raw = message?.createdAt ?? message?.created_at ?? null
  let timeString = ''
  
  // Extract file data if present
  let fileData = null
  try {
    if (message.file_data) {
      fileData = JSON.parse(message.file_data)
    }
  } catch (e) {
    console.error("Error parsing file data:", e)
  }
  
  // Get file URL
  const fileUrl = message.file_url

  if (raw != null) {
    const d = new Date(raw)
    if (!Number.isNaN(d.getTime())) {
      timeString = d.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      })
    }
  }
  return (
    <div className={`flex mt-2 ${isOwnMessage ? 'justify-end' : 'justify-start'}`}>
      <div
        className={cn('max-w-[75%] w-fit flex flex-col gap-1', {
          'items-end': isOwnMessage,
        })}>
        {showHeader && (
          <div
            className={cn('flex items-center gap-2 text-xs px-3', {
              'justify-end flex-row-reverse': isOwnMessage,
            })}>
            <span className={'font-medium'}>{userName}</span>
            <span className="text-foreground/50 text-xs">{timeString}</span>
          </div>
        )}
        <div
          className={cn(
            'py-2 px-3 rounded-xl text-sm w-fit',
            isOwnMessage ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
          )}>
          {message.content}
          
          {/* File attachment display */}
          {fileData && (
            <div className="mt-2 flex items-center p-2 bg-background/20 rounded-md text-xs">
              <FileText className="h-3 w-3 mr-2" />
              <span className="flex-1 truncate">{fileData.fileName}</span>
              {fileUrl && (
                <a 
                  href={fileUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="ml-2 opacity-70 hover:opacity-100"
                >
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          )}
          
          {/* If the message was optimistically added and is still being inserted
              into the DB, show a subtle sending indicator. The hook will replace
              this optimistic message with the persisted row once the Postgres
              subscription or insert response confirms the insertion. */}
          {message._status === 'sending' ? (
            <div className="text-[10px] opacity-70 mt-1">sending...</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
