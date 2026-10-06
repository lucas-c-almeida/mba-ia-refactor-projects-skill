'use strict';

const crypto = require('node:crypto');
const { promisify } = require('node:util');

// One-way password storage with a salted KDF from the standard library (AP-08, RP-08).
const scrypt = promisify(crypto.scrypt);

const SALT_BYTES = 16;
const KEY_BYTES = 64;
const GENERATED_PASSWORD_BYTES = 24;
const SCHEME = 'scrypt';

async function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const key = await scrypt(password, salt, KEY_BYTES);
    return `${SCHEME}$${salt.toString('hex')}$${key.toString('hex')}`;
}

// For accounts created without a password: an unguessable one, never a shared default.
function generatePassword() {
    return crypto.randomBytes(GENERATED_PASSWORD_BYTES).toString('base64url');
}

module.exports = { hashPassword, generatePassword };
