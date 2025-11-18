export default function Sidebar({ sessions, currentSessionId, sessionPdfs, selectedPdf }) {
  return (
    <aside className="sidebar">
      <h2 className="sidebar-title">Chats</h2>

      <button className="new-chat-btn">+ Nuevo chat</button>

      <ul className="session-list">
        {Object.entries(sessions).map(([sid, name]) => (
          <li key={sid}>
            <a
              className={`session-item ${sid === currentSessionId ? "active" : ""}`}
            >
              {name}
            </a>
          </li>
        ))}
      </ul>

      <h3 className="sidebar-subtitle">Documentos Cargados</h3>

      <ul className="pdf-list">
        {sessionPdfs.map(pdf => (
          <li key={pdf} className={`pdf-item ${pdf === selectedPdf ? "selected" : ""}`}>
            {pdf}
          </li>
        ))}
      </ul>
    </aside>
  );
}
