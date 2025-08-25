import { cn } from '@/lib/utils'

export const ChatMessageItem = ({
  message,
  isOwnMessage,
  showHeader
}) => {
  const userName = message?.user?.name ?? ''
  const raw = message?.createdAt ?? message?.created_at ?? null
  let timeString = ''

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
        </div>
      </div>
    </div>
  );
}
