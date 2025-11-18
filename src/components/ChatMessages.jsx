import ReactMarkdown from "react-markdown";

export default function ChatMessage({ sender, message }) {
  const isBot = sender === "Bot" || sender === "📂";

  return (
    <div className={`chat-bubble ${isBot ? "bot" : "user"}`}>
      <div className="bubble-content">
        <ReactMarkdown>{message}</ReactMarkdown>
      </div>
    </div>
  );
}
