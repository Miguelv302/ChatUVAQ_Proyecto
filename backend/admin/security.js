// security.js
const bcrypt = require('bcrypt');
const rateLimit = require('express-rate-limit');
const Joi = require('joi');

const SALT_ROUNDS = 12;

async function hashPassword(password) {
  return bcrypt.hash(password, SALT_ROUNDS);
}

async function verifyPassword(password, hash) {
  return bcrypt.compare(password, hash);
}

/**
 * Middleware: requireAuth
 */
function requireAuth(req, res, next) {
  if (req.session && req.session.user && req.session.user.id) {
    return next();
  }
  return res.status(401).json({ error: 'Unauthorized' });
}

/**
 * Rate limiter for login (protect against brute force)
 */
const loginRateLimiter = rateLimit({
  windowMs: (process.env.RATE_LIMIT_WINDOW_MIN ? parseInt(process.env.RATE_LIMIT_WINDOW_MIN) : 15) * 60 * 1000,
  max: 5, // 5 intentos por IP por window
  standardHeaders: true,
  legacyHeaders: false,
  message: 'Too many login attempts, try later',
});

/**
 * Generic rate limiter for admin endpoints
 */
const strictRateLimiter = rateLimit({
  windowMs: (process.env.RATE_LIMIT_WINDOW_MIN ? parseInt(process.env.RATE_LIMIT_WINDOW_MIN) : 15) * 60 * 1000,
  max: (process.env.RATE_LIMIT_MAX ? parseInt(process.env.RATE_LIMIT_MAX) : 100),
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Joi Schemas
 */
const loginSchema = Joi.object({
  username: Joi.string().min(3).max(80).required(),
  password: Joi.string().min(8).required(),
});

const versionSchema = Joi.object({
  name: Joi.string().min(1).max(200).required(),
  meta: Joi.object().optional()
});

module.exports = {
  hashPassword,
  verifyPassword,
  requireAuth,
  loginRateLimiter,
  strictRateLimiter,
  loginSchema,
  versionSchema
};
