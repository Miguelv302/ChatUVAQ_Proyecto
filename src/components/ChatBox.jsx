import { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessages";

export default function ChatBox({ chatHistory, isLoading }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, isLoading]);

  return (
    <div className="chat-box">
      {chatHistory.map((msg, i) => (
        <ChatMessage key={i} sender={msg.sender} message={msg.message} />
      ))}

      {isLoading && (
        <div className="chat-bubble bot">
          <div className="bubble-content">...</div>
        </div>
      )}

      <div ref={endRef}></div>
    </div>
  );
}
