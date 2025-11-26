export default function AdminLayout({ onBack }) {
  return (
    <div className="admin-layout">

      <h1 className="admin-title">BIENVENIDO USUARIO</h1>

      {/* BUSCADOR */}
      <div className="admin-search">
        <input
          type="text"
          className="admin-search-input"
          placeholder=""
        />
        <button className="admin-search-btn">➤</button>
      </div>

      {/* TABLA */}
      <div className="admin-table-box">
        <table className="admin-table">
          <thead>
            <tr>
              <th></th>
              <th>Name</th>
              <th>Version</th>
              <th>Container</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            <tr>
              <td><input type="checkbox" /></td>
              <td>Precio de las colegiaturas</td>
              <td>V1</td>
              <td><a href="#">Precio de las colegiaturas</a></td>
              <td>🗑️</td>
            </tr>

            <tr>
              <td><input type="checkbox" /></td>
              <td>Precio de las colegiaturas</td>
              <td>V1</td>
              <td><a href="#">Precio de las colegiaturas</a></td>
              <td>🗑️</td>
            </tr>

            <tr>
              <td><input type="checkbox" /></td>
              <td>Precio de las colegiaturas</td>
              <td>V1</td>
              <td><a href="#">Precio de las colegiaturas</a></td>
              <td>🗑️</td>
            </tr>
          </tbody>
        </table>
      </div>

      <button className="login-submit" onClick={onBack}>
        Volver al chat
      </button>

    </div>
  );
}
