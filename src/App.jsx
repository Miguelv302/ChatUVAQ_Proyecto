import React, { useState, useEffect, useRef } from "react";
import ChatContainer from "./components/ChatContainer";
import Sidebar from "./components/sidebar";
import ChatMessage from "./components/ChatMessages";
import ChatBox from "./components/ChatBox";
import UploadForm from "./components/UploadForm";
import MessageForm from "./components/MessageForm";
import "./App.css";

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

  const handleSendMessage = async (messageText, pdfForMessage) => {
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

  return (
    <div className="app-container">

      {/* Barra amarilla con logo */}
      <header className="topbar">
        <img src="/logo_uvaq.png" className="logo-img" alt="logo" />
      </header>

      <div className="content-wrapper">
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          sessionPdfs={sessionPdfs[currentSessionId]}
          selectedPdf={selectedPdf}
        />

        <ChatContainer
          chatHistory={chatHistory}
          sessionPdfs={sessionPdfs[currentSessionId]}
          selectedPdf={selectedPdf}
          onSelectedPdfChange={setSelectedPdf}
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
