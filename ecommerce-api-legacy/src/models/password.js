'use strict';

const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);

// Password storage with the runtime's built-in KDF: per-password random salt, one-way (RP-08).
const SCHEME = 'scrypt';
const SALT_BYTES = 16;
const KEY_BYTES = 64;

async function hashPassword(plainPassword) {
  const salt = crypto.randomBytes(SALT_BYTES);
  const key = await scrypt(plainPassword, salt, KEY_BYTES);
  return `${SCHEME}$${salt.toString('hex')}$${key.toString('hex')}`;
}

/**
 * Stored when an account is created without a password: it is not in the scheme's format, so no
 * password can ever match it.
 */
function unusablePasswordHash() {
  return `!${crypto.randomBytes(SALT_BYTES).toString('hex')}`;
}

module.exports = { hashPassword, unusablePasswordHash };
