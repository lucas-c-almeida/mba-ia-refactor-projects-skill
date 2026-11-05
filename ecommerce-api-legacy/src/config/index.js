'use strict';

// Configuration: the only module that reads the process environment (RP-01).
// Read once at startup, validated, and frozen.

const DEFAULT_PORT = 3000;
const MAX_PORT = 65535;

// The datastore is an in-process SQLite database rebuilt (schema + seed) at every start.
// Kept as a constant: making it a file would change what survives a restart.
const DATABASE_FILE = ':memory:';

class ConfigError extends Error {}

/** A secret is "configured" only when it is non-empty; an empty value means unset (fail closed). */
function readSecret(env, name) {
  const value = typeof env[name] === 'string' ? env[name].trim() : '';
  return value === '' ? null : value;
}

function readPort(env) {
  const raw = env.PORT;
  if (raw === undefined || raw === '') return DEFAULT_PORT;
  if (!/^\d+$/.test(raw) || Number(raw) < 1 || Number(raw) > MAX_PORT) {
    throw new ConfigError(`PORT must be an integer between 1 and ${MAX_PORT}, got: ${raw}`);
  }
  return Number(raw);
}

function loadConfig(env = process.env) {
  return Object.freeze({
    port: readPort(env),
    databaseFile: DATABASE_FILE,
    // Operator credential guarding privileged routes. Unset by default: those routes answer 403.
    operatorToken: readSecret(env, 'OPERATOR_TOKEN'),
  });
}

module.exports = { loadConfig, ConfigError };
