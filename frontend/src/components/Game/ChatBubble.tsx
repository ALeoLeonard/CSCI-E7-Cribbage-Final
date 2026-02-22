import { useState, useRef, useEffect } from 'react';
import { useLobbyStore } from '../../store/lobbyStore';

export function ChatBubble() {
  const { chatMessages, sendChat } = useLobbyStore();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [unread, setUnread] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      setUnread(0);
      scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
    } else if (chatMessages.length > 0 && chatMessages[chatMessages.length - 1].from === 'opponent') {
      setUnread((u) => u + 1);
    }
  }, [chatMessages, open]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;
    sendChat(text);
    setInput('');
  };

  return (
    <div className="fixed bottom-3 left-3 z-40">
      {open ? (
        <div className="bg-felt-dark border border-white/10 rounded-xl shadow-2xl w-64 flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 border-b border-white/10">
            <span className="text-sm font-bold">Chat</span>
            <button onClick={() => setOpen(false)} className="text-white/50 hover:text-white text-lg leading-none">&times;</button>
          </div>
          <div ref={scrollRef} className="flex-1 max-h-40 overflow-y-auto px-3 py-2 space-y-1 text-xs">
            {chatMessages.length === 0 && (
              <span className="text-white/30 italic">No messages yet</span>
            )}
            {chatMessages.map((m, i) => (
              <div key={i} className={`${m.from === 'me' ? 'text-right text-blue-300' : 'text-left text-green-300'}`}>
                <span className="bg-white/5 rounded px-2 py-0.5 inline-block max-w-[200px] break-words">
                  {m.text}
                </span>
              </div>
            ))}
          </div>
          <form onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            className="flex border-t border-white/10">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              maxLength={100}
              placeholder="Type a message..."
              className="flex-1 bg-transparent px-3 py-2 text-xs outline-none placeholder:text-white/30"
            />
            <button type="submit" className="px-3 text-gold text-xs font-bold hover:text-yellow-400">
              Send
            </button>
          </form>
        </div>
      ) : (
        <button
          onClick={() => { setOpen(true); setUnread(0); }}
          className="bg-felt-dark border border-white/10 rounded-full w-10 h-10 flex items-center justify-center
                     shadow-lg hover:bg-white/10 transition-colors relative"
        >
          <span className="text-lg">💬</span>
          {unread > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
              {unread}
            </span>
          )}
        </button>
      )}
    </div>
  );
}
