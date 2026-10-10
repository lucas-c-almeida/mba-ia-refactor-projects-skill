// Reads the environment once and exposes an immutable object (RP-01, RP-17).
// Nothing else in the codebase reads process.env.

const DEFAULT_PORT = 3000;

function parsePort(raw) {
    if (raw === undefined || raw === '') return DEFAULT_PORT;
    const port = Number(raw);
    if (!Number.isInteger(port) || port <= 0 || port > 65535) {
        throw new Error(`invalid PORT: ${raw}`);
    }
    return port;
}

function loadConfig(env = process.env) {
    return Object.freeze({
        port: parsePort(env.PORT),
        // Operator credential for privileged routes. Unset by default: the guard stays closed (403).
        operatorToken: env.OPERATOR_TOKEN || null,
    });
}

module.exports = { loadConfig, DEFAULT_PORT };
