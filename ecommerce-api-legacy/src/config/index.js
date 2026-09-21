// Configuration: the only module that reads the environment (AP-01, AP-06, AP-15 — RP-01).
// Read once at startup, validated, frozen. No secret has a literal default.

class ConfigError extends Error {}

const DEFAULT_PORT = 3000; // the port the application has always listened on

function parsePort(raw) {
    if (raw === undefined || raw === '') return DEFAULT_PORT;
    const port = Number(raw);
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
        throw new ConfigError(`invalid PORT: ${raw}`);
    }
    return port;
}

function loadConfig(env = process.env) {
    return Object.freeze({
        port: parsePort(env.PORT),
        // Password for the seeded demo account. When unset, the seed gets a random password,
        // so no account ships with a known credential.
        seedUserPassword: env.SEED_USER_PASSWORD || null,
    });
}

module.exports = { loadConfig, ConfigError };
