
export default function Login({ onBack, onLogin }) {

  return (
    <div className="login-box">
      <div className="login-icon">
        <span className="material-icons login-user-icon">person</span>
      </div>

      <h3 className="login-title">USER</h3>
      <input type="text" className="login-field" />

      <h3 className="login-title">PASSWORD</h3>
      <input type="password" className="login-field" />

      <button className="login-submit" onClick={onLogin}>ENVIAR</button>

      <button className="login-back-btn" onClick={onBack}>
        Volver al chat
      </button>
    </div>
  );
}
