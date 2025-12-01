import React, { useState } from "react";
import ChatContainer from "./components/ChatContainer";
import Sidebar from "./components/Sidebar";
import "./App.css";
import Login from "./components/Login";
import AdminLayout from "./components/Admin";



// Mocks
const mockSessions = { 'sid-1': 'Chat sobre IA' };
const mockSessionPdfs = { 'sid-1': ['doc_ia.pdf'] };
const mockChatHistory = [
  { sender: 'Tú', message: 'Hola, ¿puedes resumir doc_ia.pdf?' },
  { sender: 'Bot', message: 'Claro, este documento trata sobre...' }
];

const MOCK_CURRENT_SESSION_ID = 'sid-1';
const MOCK_SELECTED_PDF = 'doc_ia.pdf';

export default function ChatApp() {
  const [sessions] = useState(mockSessions);
  const [currentSessionId] = useState(MOCK_CURRENT_SESSION_ID);
  const [sessionPdfs, setSessionPdfs] = useState(mockSessionPdfs);
  const [selectedPdf, setSelectedPdf] = useState(MOCK_SELECTED_PDF);
  const [chatHistory, setChatHistory] = useState(mockChatHistory);
  const [isLoading, setIsLoading] = useState(false);
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [isAdminLogged, setIsAdminLogged] = useState(false);




  const handleSendMessage = async (messageText) => {
    if (!messageText) return;

    setChatHistory(prev => [...prev, { sender: "Tú", message: messageText }]);
    setIsLoading(true);

    await new Promise(r => setTimeout(r, 1200));

    setChatHistory(prev => [
      ...prev,
      { sender: "Bot", message: `Respuesta sobre "${messageText}".` }
    ]);

    setIsLoading(false);
  };

  const handleFileUpload = async (file) => {
    if (!file) return;

    setChatHistory(prev => [
      ...prev,
      { sender: "📂", message: `Subiendo archivo ${file.name}...` }
    ]);

    await new Promise(r => setTimeout(r, 1500));

    setChatHistory(prev =>
      prev.map(m =>
        m.message.includes("Subiendo archivo")
          ? { sender: "📂", message: `Archivo ${file.name} cargado correctamente.` }
          : m
      )
    );

    setSessionPdfs(prev => ({
      ...prev,
      [currentSessionId]: [...prev[currentSessionId], file.name]
    }));
  };

  if (showAdminLogin && !isAdminLogged) {
    return (
      <div className="app-container">
        <header className="topbar">
          <img src="/logo_uvaq.png" className="logo-img" alt="logo" />
        </header>

        <main className="content-wrapper login-center">
          <Login
            onBack={() => setShowAdminLogin(false)}
            onLogin={() => setIsAdminLogged(true)}
          />
        </main>
      </div>
    );
  }

  if (isAdminLogged) {
    return (
      <div className="app-container">
        <header className="topbar">
          <img src="/logo_uvaq.png" className="logo-img" alt="logo" />
        </header>

        <main className="content-wrapper login-center">
          <AdminLayout 
            onBack={() => {
              setIsAdminLogged(false);
              setShowAdminLogin(false);
            }} 
          />
        </main>
      </div>
    );
  }


  
  return (
    <div className="app-container">

      {/* TOP BAR */}
      <header className="topbar">
        <img src="/logo_uvaq.png" className="logo-img" alt="logo" />
      </header>

      {/* LAYOUT COMO CHATGPT */}
      <div className="layout">

        
        {/* SIDEBAR (FIJO A LA IZQUIERDA) */}
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          sessionPdfs={sessionPdfs[currentSessionId]}
          selectedPdf={selectedPdf}

          onAdminClick={() => setShowAdminLogin(true)}
        />

        {/* CONTENIDO PRINCIPAL DE CHAT */}
        <main className="content-wrapper">
          <ChatContainer
            chatHistory={chatHistory}
            sessionPdfs={sessionPdfs[currentSessionId]}
            selectedPdf={selectedPdf}
            onSelectedPdfChange={setSelectedPdf}
            onSendMessage={handleSendMessage}
            onFileUpload={handleFileUpload}
            isLoading={isLoading}
          />
        </main>

      </div>

    </div>
  );
}
