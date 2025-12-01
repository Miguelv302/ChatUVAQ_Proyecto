// server.js
require('dotenv').config();
const express = require('express');
const helmet = require('helmet');
const session = require('express-session');
const PgSession = require('connect-pg-simple')(session);
const { pool, initTables, getVersions, createVersion, deleteVersion, activateVersion, logAction, query } = require('./db');
const {
  hashPassword,
  verifyPassword,
  requireAuth,
  loginRateLimiter,
  strictRateLimiter,
  loginSchema,
  versionSchema
} = require('./security');

const app = express();
const PORT = process.env.PORT || 4000;

// Middlewares
app.use(helmet());
app.use(express.json());

// Session store (Postgres)
app.use(session({
  store: new PgSession({
    pool: pool,
    tableName: process.env.SESSION_TABLE_NAME || 'session'
  }),
  secret: process.env.SESSION_SECRET || 'cambia_esto',
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: parseInt(process.env.SESSION_MAX_AGE || '86400000') // 1 día por defecto
  }
}));

// Simple health
app.get('/health', (req, res) => res.json({ ok: true }));

/**
 * INITIAL SETUP: create tables and ensure an admin user exists (solo en dev puede crear uno por defecto)
 */
(async function startup() {
  await initTables();
  // create default admin if none exists (solo si no hay usuarios)
  const r = await query('SELECT COUNT(*) FROM admin_users');
  const count = parseInt(r.rows[0].count, 10);
  if (count === 0) {
    const defaultUser = process.env.DEFAULT_ADMIN_USER || 'admin';
    const defaultPass = process.env.DEFAULT_ADMIN_PASS || 'Admin12345!'; // cambia en prod
    const pwHash = await hashPassword(defaultPass);
    await query('INSERT INTO admin_users (username, password_hash) VALUES ($1, $2)', [defaultUser, pwHash]);
    console.log(`[BOOT] Usuario admin creado: ${defaultUser} (cambia contraseña en entorno)`);
  }
  console.log('Inicialización DB completada');
})().catch(err => {
  console.error('Error al inicializar:', err);
  process.exit(1);
});

/**
 * LOGIN
 */
app.post('/login', loginRateLimiter, async (req, res) => {
  const { error, value } = loginSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details.map(d=>d.message).join(', ') });

  const { username, password } = value;
  const result = await query('SELECT id, username, password_hash FROM admin_users WHERE username = $1', [username]);
  if (result.rowCount === 0) {
    return res.status(401).json({ error: 'Credenciales inválidas' });
  }
  const user = result.rows[0];
  const ok = await verifyPassword(password, user.password_hash);
  if (!ok) {
    await logAction({ user_id: user.id, action: 'failed_login', meta: { username } });
    return res.status(401).json({ error: 'Credenciales inválidas' });
  }
  // set session
  req.session.user = { id: user.id, username: user.username };
  await logAction({ user_id: user.id, action: 'login_success', meta: { username } });
  return res.json({ ok: true, user: { id: user.id, username: user.username } });
});

/**
 * LOGOUT
 */
app.post('/logout', requireAuth, async (req, res) => {
  const uid = req.session.user?.id;
  req.session.destroy(err => {
    if (err) {
      return res.status(500).json({ error: 'Error cerrando sesión' });
    }
  });
  await logAction({ user_id: uid, action: 'logout' });
  return res.json({ ok: true });
});

/**
 * RUTAS DE VERSIONS - todas protegidas
 */
app.get('/versions', requireAuth, strictRateLimiter, async (req, res) => {
  const rows = await getVersions();
  return res.json({ versions: rows });
});

app.post('/versions/create', requireAuth, strictRateLimiter, async (req, res) => {
  const { error, value } = versionSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details.map(d=>d.message).join(', ') });
  const created = await createVersion({ name: value.name, meta: value.meta || {} });
  await logAction({ user_id: req.session.user.id, action: 'create_version', meta: { id: created.id, name: created.name } });
  return res.json({ ok: true, version: created });
});

app.post('/versions/delete', requireAuth, strictRateLimiter, async (req, res) => {
  const { id } = req.body;
  if (!id) return res.status(400).json({ error: 'id requerido' });
  await deleteVersion(id);
  await logAction({ user_id: req.session.user.id, action: 'delete_version', meta: { id } });
  return res.json({ ok: true });
});

app.post('/versions/activate', requireAuth, strictRateLimiter, async (req, res) => {
  const { id } = req.body;
  if (!id) return res.status(400).json({ error: 'id requerido' });
  const activated = await activateVersion(id);
  await logAction({ user_id: req.session.user.id, action: 'activate_version', meta: { id: activated.id } });
  return res.json({ ok: true, version: activated });
});

/**
 * TEST a la version: endpoint que el admin puede usar para "probar" la versión activa o una en específico.
 * Aquí sólo simulamos — la integración real con Qdrant / LMStudio se implementa en el servicio de entrenamiento.
 */
app.get('/versions/test/:id', requireAuth, strictRateLimiter, async (req, res) => {
  const id = req.params.id;
  const versions = await query('SELECT * FROM versions WHERE id = $1', [id]);
  if (versions.rowCount === 0) return res.status(404).json({ error: 'Version no encontrada' });

  // Simulación de prueba:
  const v = versions.rows[0];
  await logAction({ user_id: req.session.user.id, action: 'test_version', meta: { id: v.id, name: v.name } });

  return res.json({ ok: true, tested: { id: v.id, name: v.name, active: v.active } , note: 'Esto es una prueba simulada. Implementa test real en integración con el servicio de RAG/LM.'});
});

/**
 * Ruta para listar logs (protege por ser admin)
 */
app.get('/logs', requireAuth, strictRateLimiter, async (req, res) => {
  const r = await query('SELECT id, user_id, action, action_hash, created_at, meta FROM admin_logs ORDER BY created_at DESC LIMIT 200');
  return res.json({ logs: r.rows });
});

app.listen(PORT, () => {
  console.log(`Admin server corriendo en http://localhost:${PORT}`);
});
