'use strict';

// The only module that reads the environment. Everything else receives this object.
// No secret lives in source: the application currently needs none (AP-01, RP-01).

const DEFAULT_PORT = 3000; // the port the application has always listened on
const IN_MEMORY_DATABASE = ':memory:';

class ConfigError extends Error {}

function parsePort(raw) {
    if (raw === undefined || raw === '') return DEFAULT_PORT;
    const port = Number(raw);
    if (!Number.isInteger(port) || port <= 0 || port > 65535) {
        throw new ConfigError(`invalid PORT: ${raw}`);
    }
    return port;
}

function loadConfig(env = process.env) {
    return Object.freeze({
        port: parsePort(env.PORT),
        databaseFile: env.DATABASE_FILE || IN_MEMORY_DATABASE,
    });
}

module.exports = { loadConfig, ConfigError };
