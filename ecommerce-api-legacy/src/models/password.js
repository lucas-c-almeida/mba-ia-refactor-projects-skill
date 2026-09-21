// One-way password storage (AP-08 — RP-08), using the runtime's own scrypt KDF:
// per-credential random salt, tunable work factor, no added dependency.
// Stored format: scrypt$<salt hex>$<derived key hex>.

const crypto = require('crypto');

const SALT_BYTES = 16;
const KEY_BYTES = 32;
const RANDOM_PASSWORD_BYTES = 24;

function hashPassword(password) {
    return new Promise((resolve, reject) => {
        const salt = crypto.randomBytes(SALT_BYTES);
        crypto.scrypt(password, salt, KEY_BYTES, (err, key) => {
            if (err) return reject(err);
            resolve(`scrypt$${salt.toString('hex')}$${key.toString('hex')}`);
        });
    });
}

// For an account that must exist but must not have a known credential (the seed, when no
// password is configured).
function randomPassword() {
    return crypto.randomBytes(RANDOM_PASSWORD_BYTES).toString('base64url');
}

module.exports = { hashPassword, randomPassword };
