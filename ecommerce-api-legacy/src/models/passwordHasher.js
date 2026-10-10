const crypto = require('crypto');

const SALT_BYTES = 16;
const KEY_BYTES = 64;
const GENERATED_SECRET_BYTES = 16;

function scrypt(password, salt) {
    return new Promise((resolve, reject) => {
        crypto.scrypt(password, salt, KEY_BYTES, (err, key) => (err ? reject(err) : resolve(key)));
    });
}

// One-way password storage with a per-credential salt: "scrypt$<salt hex>$<key hex>".
async function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES);
    const key = await scrypt(password, salt);
    return `scrypt$${salt.toString('hex')}$${key.toString('hex')}`;
}

// A password nobody knows: used where the account has no password of its own (no known default).
function generateUnusableSecret() {
    return crypto.randomBytes(GENERATED_SECRET_BYTES).toString('hex');
}

// The collaborator handed to the controller and the seed (wired in the composition root).
const passwords = Object.freeze({ hash: hashPassword, generateSecret: generateUnusableSecret });

module.exports = { passwords };
