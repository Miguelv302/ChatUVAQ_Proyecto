// server.js
require('dotenv').config();
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const session = require('express-session');
const PgSession = require('connect-pg-simple')(session);

const {
  pool,
  initTables,
  getVersions,
  createVersion,
  deleteVersion,
  activateVersion,
  logAction,
  query
} = require('./db');

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

// ----------------------------------
// 🔥 CORS FIX para React + Cookies
// ----------------------------------
app.use(cors({
  origin: "http://localhost:5173", // tu frontend
  credentials: true
}));

// Middlewares
app.use(helmet());
app.use(express.json());

// Sessions
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
    maxAge: parseInt(process.env.SESSION_MAX_AGE || '86400000')
  }
}));

// Health
app.get('/health', (req, res) => res.json({ ok: true }));

// Init
(async function startup() {
  await initTables();
  const r = await query('SELECT COUNT(*) FROM admin_users');
  const count = parseInt(r.rows[0].count, 10);

  if (count === 0) {
    const defaultUser = process.env.DEFAULT_ADMIN_USER || 'admin';
    const defaultPass = process.env.DEFAULT_ADMIN_PASS || 'Admin12345!';
    const pwHash = await hashPassword(defaultPass);

    await query(
      'INSERT INTO admin_users (username, password_hash) VALUES ($1, $2)',
      [defaultUser, pwHash]
    );

    console.log(`[BOOT] Usuario admin creado: ${defaultUser}`);
  }

  console.log('Inicialización DB completada');
})();


// ----------------------------------
// LOGIN
// ----------------------------------
app.post('/login', loginRateLimiter, async (req, res) => {
  const { error, value } = loginSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details.map(d => d.message).join(', ') });

  const { username, password } = value;

  const result = await query(
    'SELECT id, username, password_hash FROM admin_users WHERE username = $1',
    [username]
  );

  if (result.rowCount === 0)
    return res.status(401).json({ error: 'Credenciales inválidas' });

  const user = result.rows[0];

  const ok = await verifyPassword(password, user.password_hash);
  if (!ok)
    return res.status(401).json({ error: 'Credenciales inválidas' });

  req.session.user = { id: user.id, username: user.username };

  return res.json({ ok: true, user: { id: user.id, username: user.username } });
});

// Logout
app.post('/logout', requireAuth, async (req, res) => {
  req.session.destroy(() => {});
  return res.json({ ok: true });
});

// Versions
app.get('/versions', requireAuth, strictRateLimiter, async (req, res) => {
  const rows = await getVersions();
  return res.json({ versions: rows });
});

app.post('/versions/create', requireAuth, strictRateLimiter, async (req, res) => {
  const { error, value } = versionSchema.validate(req.body);
  if (error) return res.status(400).json({ error: error.details.map(d => d.message).join(', ') });

  const created = await createVersion({ name: value.name, meta: value.meta || {} });
  return res.json({ ok: true, version: created });
});

app.post('/versions/delete', requireAuth, strictRateLimiter, async (req, res) => {
  const { id } = req.body;
  if (!id) return res.status(400).json({ error: 'id requerido' });

  await deleteVersion(id);
  return res.json({ ok: true });
});

app.post('/versions/activate', requireAuth, strictRateLimiter, async (req, res) => {
  const { id } = req.body;
  if (!id) return res.status(400).json({ error: 'id requerido' });

  const activated = await activateVersion(id);
  return res.json({ ok: true, version: activated });
});

// Logs
app.get('/logs', requireAuth, strictRateLimiter, async (req, res) => {
  const r = await query('SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT 200');
  return res.json({ logs: r.rows });
});

app.listen(PORT, () => {
  console.log(`Admin server corriendo en http://localhost:${PORT}`);
});
