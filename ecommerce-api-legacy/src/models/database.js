'use strict';

const sqlite3 = require('sqlite3');

/** Promise form of the three driver calls, bound to one connection. */
function statementsOf(connection) {
  return {
    run(sql, params = []) {
      return new Promise((resolve, reject) => {
        connection.run(sql, params, function onRun(err) {
          if (err) return reject(err);
          return resolve({ lastId: this.lastID, changes: this.changes });
        });
      });
    },
    get(sql, params = []) {
      return new Promise((resolve, reject) => {
        connection.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
      });
    },
    all(sql, params = []) {
      return new Promise((resolve, reject) => {
        connection.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
      });
    },
  };
}

/**
 * One SQLite connection. Statements always take a parameter array: values are bound by the
 * driver, never concatenated into SQL.
 *
 * A transaction on a single connection would also capture any statement another request sends
 * while it is open. So every statement outside a transaction waits until no transaction is open,
 * and the statements of a transaction go through the handle `transaction` gives to its work.
 */
class Database {
  constructor(connection) {
    this.statements = statementsOf(connection);
    this.pendingTransactions = Promise.resolve();
  }

  static open(filename) {
    return new Promise((resolve, reject) => {
      const connection = new sqlite3.Database(filename, (err) => (
        err ? reject(err) : resolve(new Database(connection))
      ));
    });
  }

  run(sql, params) {
    return this.pendingTransactions.then(() => this.statements.run(sql, params));
  }

  get(sql, params) {
    return this.pendingTransactions.then(() => this.statements.get(sql, params));
  }

  all(sql, params) {
    return this.pendingTransactions.then(() => this.statements.all(sql, params));
  }

  /**
   * Runs `work(tx)` inside BEGIN/COMMIT, where `tx` has the same run/get/all methods. Transactions
   * run one at a time. On failure the transaction is rolled back and the original error rethrown.
   */
  transaction(work) {
    const tx = this.statements;
    const result = this.pendingTransactions.then(async () => {
      await tx.run('BEGIN');
      try {
        const value = await work(tx);
        await tx.run('COMMIT');
        return value;
      } catch (err) {
        await rollbackAfter(tx, err);
        throw err;
      }
    });
    // The chain only orders transactions; each caller receives its own outcome through `result`.
    this.pendingTransactions = result.then(() => undefined, () => undefined);
    return result;
  }
}

async function rollbackAfter(tx, originalError) {
  try {
    await tx.run('ROLLBACK');
  } catch (rollbackError) {
    // Deliberate and narrow: the original error is the one rethrown to the caller; the rollback
    // failure is attached to it so the error boundary logs both.
    originalError.rollbackError = rollbackError;
  }
}

module.exports = { Database };
