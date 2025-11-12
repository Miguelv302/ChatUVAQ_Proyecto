import React, { useState, useEffect, useRef } from 'react';
// Necesitarás instalar react-markdown para renderizar el markdown
// npm install react-markdown
import ReactMarkdown from 'react-markdown';
import './App.css';

// --- Datos de ejemplo (lo que antes venía de Jinja2) ---
const mockSessions = {
  'sid-1': 'Chat sobre IA',
  'sid-2': 'Documento de Finanzas',
};
const mockSessionPdfs = {
  'sid-1': ['doc_ia.pdf'],
  'sid-2': ['reporte_q3.pdf', 'balance_2024.pdf'],
};
const mockChatHistory = [
  { sender: 'Tú', message: 'Hola, ¿puedes resumir doc_ia.pdf?' },
  { sender: 'Bot', message: 'Claro, el documento trata sobre los avances recientes en modelos de lenguaje grandes.' }
];
const MOCK_CURRENT_SESSION_ID = 'sid-1';
const MOCK_SELECTED_PDF = 'doc_ia.pdf';

// ------------------------------------
// --- Componente Principal de la App ---
// ------------------------------------
export default function ChatApp() {
  // --- Estado de React ---
  // Estos estados reemplazan los datos que venían de Jinja2 y el estado implícito del DOM
  const [sessions, setSessions] = useState(mockSessions);
  const [currentSessionId, setCurrentSessionId] = useState(MOCK_CURRENT_SESSION_ID);
  const [sessionPdfs, setSessionPdfs] = useState(mockSessionPdfs);
  const [selectedPdf, setSelectedPdf] = useState(MOCK_SELECTED_PDF);
  const [chatHistory, setChatHistory] = useState(mockChatHistory);
  
  // Estado para el mensaje en progreso (typing)
  const [isLoading, setIsLoading] = useState(false);

  // --- Lógica de Efectos ---
  // Simula el fetch inicial de datos (si fuera necesario en una SPA real)
  useEffect(() => {
    // Aquí podrías hacer un fetch a /api/sessions o /api/chat/{sessionId}
    // para cargar los datos iniciales en lugar de usar mocks.
  }, [currentSessionId]); // Se re-ejecuta si cambia la sesión

  
  // --- Manejadores de Eventos (reemplazan addEventListener) ---

  const handleNewChat = (e) => {
    e.preventDefault();
    console.log("Creando nuevo chat...");
    // TODO: Implementar llamada a la API POST /new_session
    // Luego, actualizar el estado:
    // const newSessionId = 'sid-3';
    // setSessions(prev => ({ ...prev, [newSessionId]: 'Nuevo Chat' }));
    // setCurrentSessionId(newSessionId);
    // setChatHistory([]);
    // setSessionPdfs(prev => ({ ...prev, [newSessionId]: [] }));
  };

  const handleSendMessage = async (messageText, pdfForMessage) => {
    if (!messageText) return;

    // 1. Añadir el mensaje del usuario al chat
    setChatHistory(prev => [
      ...prev,
      { sender: 'Tú', message: messageText }
    ]);
    
    // 2. Activar el indicador de "escribiendo..."
    setIsLoading(true);

    // 3. Simular llamada a la API
    // TODO: Reemplazar con la llamada fetch real
    // const response = await fetch(`/api/chat/${currentSessionId}?message_pdf=${pdfForMessage}`, { ... });
    // const data = await response.json();
    // const botResponse = data.message;
    await new Promise(resolve => setTimeout(resolve, 1500)); // Simular espera
    const botResponse = `Respuesta simulada sobre "${messageText}" y el documento "${pdfForMessage || 'todos'}".`;
    
    // 4. Quitar el indicador y añadir la respuesta del bot
    setIsLoading(false);
    setChatHistory(prev => [
      ...prev,
      { sender: 'Bot', message: botResponse }
    ]);
  };

  const handleFileUpload = async (file) => {
    if (!file) {
      setChatHistory(prev => [
        ...prev,
        { sender: '📂', message: 'Por favor, selecciona un archivo primero.' }
      ]);
      return;
    }
    
    // 1. Añadir mensaje de "subiendo..."
    const uploadMessage = `Subiendo archivo: ${file.name}...`;
    setChatHistory(prev => [
      ...prev,
      { sender: '📂', message: uploadMessage, isStatus: true }
    ]);

    // 2. Preparar y enviar la data
    const formData = new FormData();
    formData.append("pdf_file", file);
    
    // 3. Simular llamada a la API
    // TODO: Reemplazar con la llamada fetch real
    // const response = await fetch(`/api/upload/${currentSessionId}`, { ... });
    // const data = await response.json();
    // const { status, message, filename } = data;
    await new Promise(resolve => setTimeout(resolve, 2000)); // Simular subida
    const status = 'processing';
    const message = `Archivo "${file.name}" procesado correctamente.`;
    const filename = file.name;

    // 4. Actualizar el mensaje de estado
    setChatHistory(prev => prev.map(msg => 
      msg.message === uploadMessage ? { sender: '📂', message: message, isStatus: true } : msg
    ));

    // 5. Si fue exitoso, actualizar las listas de PDFs
    if (status === 'processing' && filename) {
      // Reemplaza la función addPdfToLists
      setSessionPdfs(prev => {
        const currentPdfs = prev[currentSessionId] || [];
        if (currentPdfs.includes(filename)) {
          return prev; // Ya existe, no hacer nada
        }
        return {
          ...prev,
          [currentSessionId]: [...currentPdfs, filename]
        };
      });
      // También podríamos querer seleccionarlo por defecto
      // setSelectedPdf(filename);
    }
  };
  
  // --- Renderizado ---
  return (
    <>
      <Sidebar 
        sessions={sessions}
        currentSessionId={currentSessionId}
        sessionPdfs={sessionPdfs[currentSessionId] || []}
        selectedPdf={selectedPdf}
        onNewChat={handleNewChat}
        // onSessionClick={setCurrentSessionId} // Implementar navegación
      />
      
      <ChatContainer
        chatHistory={chatHistory}
        sessionPdfs={sessionPdfs[currentSessionId] || []}
        selectedPdf={selectedPdf}
        onSelectedPdfChange={setSelectedPdf} // Permitir que el select cambie el estado
        onSendMessage={handleSendMessage}
        onFileUpload={handleFileUpload}
        isLoading={isLoading}
      />
    </>
  );
}

// ------------------------------------
// --- Componentes Hijos ---
// ------------------------------------

function Sidebar({ sessions, currentSessionId, sessionPdfs, selectedPdf, onNewChat, onSessionClick }) {
  return (
    <div className="sidebar">
      <h3>Chats</h3>
      {/* El form original era para un POST, en React usamos onClick */}
      <form onSubmit={onNewChat}>
        <button type="submit">+ Nuevo chat</button>
      </form>
      
      <ul id="session-list">
        {Object.entries(sessions).map(([sid, name]) => (
          <li key={sid}>
            {/* En una app real, esto sería un <Link> de react-router */}
            <a 
              href={`/chat/${sid}`}
              className={sid === currentSessionId ? 'active' : ''}
              onClick={(e) => {
                e.preventDefault();
                // onSessionClick(sid); // Descomentar para habilitar
                console.log(`Navegar a sesión ${sid} (no implementado)`);
              }}
            >
              {name}
            </a>
          </li>
        ))}
      </ul>
      
      <h4>Documentos Cargados</h4>
      <ul id="pdf-list">
        {sessionPdfs.map((pdf) => (
          <li 
            key={pdf} 
            className={pdf === selectedPdf ? 'selected' : ''}
          >
            {pdf}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ChatContainer({ chatHistory, sessionPdfs, selectedPdf, onSelectedPdfChange, onSendMessage, onFileUpload, isLoading }) {
  return (
    <div className="chat-container">
      <ChatBox chatHistory={chatHistory} isLoading={isLoading} />
      
      <UploadForm onFileUpload={onFileUpload} />
      
      <MessageForm 
        sessionPdfs={sessionPdfs}
        selectedPdf={selectedPdf}
        onSelectedPdfChange={onSelectedPdfChange}
        onSendMessage={onSendMessage}
      />
    </div>
  );
}

function ChatBox({ chatHistory, isLoading }) {
  // --- Lógica de Auto-Scroll ---
  // Esto reemplaza la función scrollToBottom()
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isLoading]); // Se ejecuta cada vez que los mensajes cambian
  
  return (
    <div className="chat-box" id="chat-box">
      {chatHistory.map((msg, index) => (
        <ChatMessage key={index} sender={msg.sender} message={msg.message} />
      ))}
      
      {/* Indicador de "escribiendo..." */}
      {isLoading && (
        <div className="chat-message bot typing-indicator">
          <strong>Bot:</strong>
          <div>...</div>
        </div>
      )}
      
      {/* Elemento invisible para forzar el scroll */}
      <div ref={chatEndRef} />
    </div>
  );
}

function ChatMessage({ sender, message }) {
  const isBot = sender === 'Bot' || sender === '📂';
  const senderClass = isBot ? 'bot' : 'user';
  
  return (
    <div className={`chat-message ${senderClass}`}>
      <strong>{sender}:</strong>
      {isBot ? (
        // Usamos ReactMarkdown para renderizar el mensaje del bot
        <div className="markdown-message">
          <ReactMarkdown>{message}</ReactMarkdown>
        </div>
      ) : (
        // El mensaje del usuario se muestra como texto plano
        <div>{message}</div>
      )}
    </div>
  );
}

function UploadForm({ onFileUpload }) {
  // Estado para manejar el archivo seleccionado internamente
  const [file, setFile] = useState(null);
  const fileInputRef = useRef(null); // Para resetear el input

  const handleSubmit = (e) => {
    e.preventDefault();
    onFileUpload(file);
    // Limpiar el input después de enviar
    setFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };
  
  return (
    <form id="form-upload" className="input-container" onSubmit={handleSubmit}>
      <div className="input-row">
        {/* El label sigue funcionando igual para "clickear" el input escondido */}
        <label htmlFor="pdf_file" className="boton-raro">
          📂 {file ? file.name : 'Subir Archivo'}
        </label>
        <input 
          type="file" 
          id="pdf_file" 
          name="pdf_file"
          accept="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          style={{ display: 'none' }}
          onChange={handleFileChange}
          ref={fileInputRef}
        />
        <button type="submit" disabled={!file}>Subir</button>
      </div>
    </form>
  );
}

function MessageForm({ sessionPdfs, selectedPdf, onSelectedPdfChange, onSendMessage }) {
  // Estado local para el input de texto
  const [messageText, setMessageText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSendMessage(messageText, selectedPdf);
    setMessageText(''); // Limpiar el input
  };
  
  return (
    <form id="form-message" className="input-container" onSubmit={handleSubmit}>
      <div className="input-row">
        <input 
          type="text" 
          id="message-input" 
          name="message" 
          placeholder="Escribe tu mensaje..." 
          autoComplete="off"
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
        />
        <select 
          id="pdf-select" 
          name="message_pdf" 
          className="select"
          value={selectedPdf}
          onChange={(e) => onSelectedPdfChange(e.target.value)}
        >
          <option value="">-- Todos los Documentos --</option>
          {sessionPdfs.map(pdf => (
            <option key={pdf} value={pdf}>
              {pdf}
            </option>
          ))}
        </select>
        <button type="submit" disabled={!messageText}>Enviar</button>
      </div>
    </form>
  );
}