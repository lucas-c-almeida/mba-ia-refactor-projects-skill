'use strict';

const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);

const SALT_BYTES = 16;
const KEY_BYTES = 64;
const GENERATED_SECRET_BYTES = 16;

/** One-way password storage: per-credential random salt plus a memory-hard KDF. */
async function hashPassword(plain) {
  const salt = crypto.randomBytes(SALT_BYTES);
  const key = await scrypt(plain, salt, KEY_BYTES);
  return `scrypt$${salt.toString('hex')}$${key.toString('hex')}`;
}

/** A random secret nobody knows, for accounts created without a password. */
function generateSecret() {
  return crypto.randomBytes(GENERATED_SECRET_BYTES).toString('hex');
}

module.exports = { hashPassword, generateSecret };
