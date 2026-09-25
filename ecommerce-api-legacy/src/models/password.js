'use strict';

const crypto = require('crypto');

/**
 * One-way credential storage — resolves AP-08 (src/utils.js:17-23, original: `badCrypto`,
 * a repeated base64 encoding truncated to 10 characters — reversible, not hashed at all).
 *
 * Uses Node's built-in `crypto.scrypt`: a purpose-built, salted, tunable password KDF,
 * available in the standard library — no new runtime dependency is introduced (see
 * `04-architecture-guidelines.md` §6: a fix that needs a dependency the project does not
 * already have is proposed, not applied; this one needs none).
 *
 * There is no login/authenticate endpoint anywhere in this API today that reads a stored
 * hash back, so this change is not observable on the public surface (see AP-08's Contract
 * field in reports/audit-latest.md).
 */

const KEY_LENGTH = 64;

function hashPassword(plainText) {
  const salt = crypto.randomBytes(16);
  const derived = crypto.scryptSync(plainText, salt, KEY_LENGTH);
  return `${salt.toString('hex')}:${derived.toString('hex')}`;
}

function verifyPassword(plainText, stored) {
  const [saltHex, hashHex] = String(stored).split(':');
  if (!saltHex || !hashHex) return false;
  const salt = Buffer.from(saltHex, 'hex');
  const expected = Buffer.from(hashHex, 'hex');
  const derived = crypto.scryptSync(plainText, salt, KEY_LENGTH);
  return expected.length === derived.length && crypto.timingSafeEqual(expected, derived);
}

/**
 * A random, single-use credential — resolves the AP-01 finding on src/AppManager.js:66-71
 * (original: `badCrypto(p || "123456")`, a fixed, publicly-known fallback password). Used
 * whenever checkout creates an account and the caller did not supply `pwd`.
 */
function randomCredential() {
  return crypto.randomBytes(18).toString('base64url');
}

module.exports = { hashPassword, verifyPassword, randomCredential };
