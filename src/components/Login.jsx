import { useState } from "react";

export default function Login({ onLogin , onBack }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  async function handleLogin() {
    setErrorMsg("");

    const response = await fetch("http://localhost:3001/login", {
      method: "POST",
      credentials: "include", // IMPORTANTE para enviar/recibir cookies de sesión
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      setErrorMsg(data.error || "Error al iniciar sesión");
      return;
    }

    // Sesión creada en backend → seguimos en frontend
    onLogin();
  }

  return (
    <div className="login-box">
      <div className="login-icon">
        <span className="material-icons login-user-icon">person</span>
      </div>

      <h3 className="login-title">USER</h3>
      <input
        type="text"
        className="login-field"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />

      <h3 className="login-title">PASSWORD</h3>
      <input
        type="password"
        className="login-field"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      {errorMsg && <p style={{ color: "red" }}>{errorMsg}</p>}

      <button className="login-submit" onClick={handleLogin}>
        ENVIAR
      </button>

      <button className="login-back-btn" onClick={onBack}>
        Volver al chat
      </button>
    </div>
  );
}
