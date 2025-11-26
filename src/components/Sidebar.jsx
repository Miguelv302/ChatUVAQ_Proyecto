import { useState } from "react";
import { FiMenu, FiMessageSquare, FiFileText, FiPlus,FiUser,FiSettings } from "react-icons/fi";


export default function Sidebar({ sessions, currentSessionId, sessionPdfs, selectedPdf,onAdminClick}) {
  const [isOpen, setIsOpen] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);

  const handleSelect = (itemName) => {
    setSelectedItem(itemName);
  };

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
      <button
        className={`new-chat-btn ${selectedItem === "newChat" ? "active-icon" : ""}`}
        onClick={() => handleSelect("newChat")}
      >
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
          <li
            key={pdf}
            className={`pdf-item 
              ${pdf === selectedPdf ? "selected" : ""} 
              ${selectedItem === pdf ? "active-icon" : ""}`}
            onClick={() => handleSelect(pdf)}
          >
            <FiFileText size={18} />
            {isOpen && <span>{pdf}</span>}
          </li>
        ))}
      </ul>

      {/* ⭐ NUEVOS BOTONES: ADMIN y AJUSTES */}
      <div className="sidebar-bottom">
        <button
          className={`session-item ${selectedItem === "admin" ? "active-icon" : ""}`}
          onClick={() => {
            handleSelect("admin");
            if (onAdminClick) onAdminClick();   // ← AVISA AL APP
          }}
        >
          <FiUser size={18} />
          {isOpen && <span>Administrador</span>}
        </button>

        <button
          className={`session-item ${selectedItem === "settings" ? "active-icon" : ""}`}
          onClick={() => handleSelect("settings")}
        >
          <FiSettings size={18} />
          {isOpen && <span>Ajustes</span>}
        </button>
      </div>

    </aside>
  );
}
