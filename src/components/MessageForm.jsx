import { useState } from "react";

export default function MessageForm({
  sessionPdfs,
  selectedPdf,
  onSelectedPdfChange,
  onSendMessage
}) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSendMessage(text, selectedPdf);
    setText("");
  };

  return (
    <form className="message-form" onSubmit={handleSubmit}>
      <div className="message-input-wrapper">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Escribe un mensaje…"
        />

        <button type="submit">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </form>
  );
}
