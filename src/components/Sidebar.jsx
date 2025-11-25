import { useState } from "react";
import { FiMenu, FiMessageSquare, FiFileText, FiPlus } from "react-icons/fi";


export default function Sidebar({ sessions, currentSessionId, sessionPdfs, selectedPdf}) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <aside className={isOpen ? "sidebar open" : "sidebar"}>
      
      {/* HEADER DEL SIDEBAR */}
      <div className="sidebar-header">
        <button className="toggle-btn" onClick={() => setIsOpen(!isOpen)}>
          <FiMenu size={20} />
        </button>
        {isOpen && <h2 className="sidebar-title">Chats</h2>}
      </div>

      {/* NUEVO CHAT */}
      <button className="new-chat-btn">
        <FiPlus size={18} />
        {isOpen && <span>Nuevo chat</span>}
      </button>

      {/* LISTA DE CHATS */}
      <ul className="session-list">
        {Object.entries(sessions).map(([sid, name]) => (
          <li key={sid} className="session-item-wrapper">
            <a className={`session-item ${sid === currentSessionId ? "active" : ""}`}>
              <FiMessageSquare size={18} />
              {isOpen && <span>{name}</span>}
            </a>
          </li>
        ))}
      </ul>

      {/* DOCUMENTOS */}
      <h3 className="sidebar-subtitle">
        <FiFileText size={18} />
        {isOpen && <span>Documentos Cargados</span>}
      </h3>

      <ul className="pdf-list">
        {sessionPdfs.map(pdf => (
          <li key={pdf} className={`pdf-item ${pdf === selectedPdf ? "selected" : ""}`}>
            <FiFileText size={18} />
            {isOpen && <span>{pdf}</span>}
          </li>
        ))}
      </ul>
    </aside>
  );
}
