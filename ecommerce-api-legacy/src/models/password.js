// One-way password storage with the runtime's built-in scrypt KDF and a per-password random salt.
const crypto = require('crypto');

const SALT_BYTES = 16;
const KEY_BYTES = 64;
const GENERATED_PASSWORD_BYTES = 24;

function hashPassword(plain) {
    return new Promise((resolve, reject) => {
        const salt = crypto.randomBytes(SALT_BYTES);
        crypto.scrypt(plain, salt, KEY_BYTES, (err, key) => {
            if (err) return reject(err);
            resolve(`scrypt$${salt.toString('hex')}$${key.toString('hex')}`);
        });
    });
}

// Used when an account is created without a password: nobody knows it, unlike a shared default.
function generatePassword() {
    return crypto.randomBytes(GENERATED_PASSWORD_BYTES).toString('base64url');
}

module.exports = { hashPassword, generatePassword };
