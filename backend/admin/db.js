// db.js
const { Pool } = require('pg');
const crypto = require('crypto');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  // opcional: ssl: { rejectUnauthorized: false } para prod si usa SSL
});

async function query(text, params) {
  const res = await pool.query(text, params);
  return res;
}

/**
 * Init minimal tables
 */
async function initTables() {
  await query(`
    CREATE TABLE IF NOT EXISTS versions (
      id SERIAL PRIMARY KEY,
      name TEXT NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
      active BOOLEAN DEFAULT false,
      meta JSONB DEFAULT '{}' 
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS admin_users (
      id SERIAL PRIMARY KEY,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
    );
  `);

  await query(`
    CREATE TABLE IF NOT EXISTS admin_logs (
      id SERIAL PRIMARY KEY,
      user_id INTEGER,
      action TEXT NOT NULL,
      action_hash TEXT NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
      meta JSONB DEFAULT '{}'
    );
  `);

  // session table used by connect-pg-simple will be created automáticamente por la librería si no existe.
}

/**
 * Versions API
 */
async function getVersions() {
  const res = await query(`SELECT * FROM versions ORDER BY created_at DESC`);
  return res.rows;
}

async function createVersion({ name, meta = {} }) {
  const res = await query(
    `INSERT INTO versions (name, meta) VALUES ($1, $2) RETURNING *`,
    [name, meta]
  );
  return res.rows[0];
}

async function deleteVersion(id) {
  await query(`DELETE FROM versions WHERE id = $1`, [id]);
  return true;
}

async function activateVersion(id) {
  // desactivar todas, activar una
  await query(`UPDATE versions SET active = false WHERE active = true`);
  const res = await query(`UPDATE versions SET active = true WHERE id = $1 RETURNING *`, [id]);
  return res.rows[0];
}

/**
 * Logging with hash
 */
function computeHash(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

async function logAction({ user_id = null, action = '', meta = {} }) {
  const textToHash = `${user_id ?? 'anon'}|${action}|${JSON.stringify(meta)}|${Date.now()}`;
  const action_hash = computeHash(textToHash);
  await query(
    `INSERT INTO admin_logs (user_id, action, action_hash, meta) VALUES ($1, $2, $3, $4)`,
    [user_id, action, action_hash, meta]
  );
  return action_hash;
}

module.exports = {
  pool,
  query,
  initTables,
  getVersions,
  createVersion,
  deleteVersion,
  activateVersion,
  logAction,
};
