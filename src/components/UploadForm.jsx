import { useState } from "react";

export default function UploadForm({ onFileUpload }) {
  const [file, setFile] = useState(null);

  const submit = e => {
    e.preventDefault();
    if (file) onFileUpload(file);
  };

  return (
    <form onSubmit={submit} className="upload-form">
      <label htmlFor="pdfUpload" className="upload-label">
        📂 {file ? file.name : "Subir archivo"}
      </label>

      <input
        id="pdfUpload"
        type="file"
        accept="application/pdf"
        onChange={e => setFile(e.target.files[0])}
        hidden
      />

      <button className="upload-btn" disabled={!file}>Subir</button>
    </form>
  );
}
