import ChatBox from "./ChatBox";
import UploadForm from "./UploadForm";
import MessageForm from "./MessageForm";

export default function ChatContainer({
  chatHistory,
  sessionPdfs,
  selectedPdf,
  onSelectedPdfChange,
  onSendMessage,
  onFileUpload,
  isLoading
}) {
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
