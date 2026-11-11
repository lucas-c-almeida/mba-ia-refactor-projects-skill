// Configuration: the only module that reads the process environment.
// It is read once, at startup, and exposed as a frozen object.

const DEFAULT_PORT = 3000;
const MAX_PORT = 65535;

class ConfigError extends Error {}

function readPort(raw) {
    if (raw === undefined || raw === '') return DEFAULT_PORT;
    const port = Number(raw);
    if (!Number.isInteger(port) || port < 1 || port > MAX_PORT) {
        throw new ConfigError(`PORT must be an integer between 1 and ${MAX_PORT}`);
    }
    return port;
}

// A secret is "configured" only when it is a non-empty value after trimming.
// Unset or empty keeps the feature that depends on it closed.
function readSecret(raw) {
    const value = typeof raw === 'string' ? raw.trim() : '';
    return value.length > 0 ? value : null;
}

function loadConfig(env) {
    return Object.freeze({
        port: readPort(env.PORT),
        // Operator credential for the privileged routes. Unset: those routes answer 403.
        operatorToken: readSecret(env.OPERATOR_TOKEN),
        // Password of the seeded demo account. Unset: a random one is generated at boot.
        seedUserPassword: readSecret(env.SEED_USER_PASSWORD),
    });
}

module.exports = { loadConfig };
