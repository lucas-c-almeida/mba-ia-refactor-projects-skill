// One-way password storage with a purpose-built KDF from the standard library. (AP-08 -> RP-08)
// Stored format: scrypt$<salt-hex>$<key-hex>. No endpoint returns it.
const crypto = require('node:crypto');

const SALT_BYTES = 16;
const KEY_BYTES = 32;

function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const key = crypto.scryptSync(password, salt, KEY_BYTES);
    return `scrypt$${salt.toString('hex')}$${key.toString('hex')}`;
}

module.exports = { hashPassword };
