// Configuration: read the environment once, validate, expose a frozen object. (AP-01/AP-06 -> RP-01)
// Nothing else in the codebase reads process.env.

class ConfigError extends Error {}

const DEFAULT_PORT = 3000;
const DEFAULT_DB_PATH = ':memory:'; // in-memory store, re-seeded on every boot (original behaviour)

function parsePort(raw) {
    if (raw === undefined || raw === '') return DEFAULT_PORT;
    const port = Number(raw);
    if (!Number.isInteger(port) || port < 0 || port > 65535) {
        throw new ConfigError(`invalid PORT: ${raw}`);
    }
    return port;
}

function loadConfig(env = process.env) {
    return Object.freeze({
        port: parsePort(env.PORT),
        dbPath: env.DB_PATH || DEFAULT_DB_PATH,
    });
}

module.exports = { loadConfig };
