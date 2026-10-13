'use strict';

const sqlite3 = require('sqlite3');

/**
 * Promise wrapper around one SQLite connection.
 *
 * Every operation goes through a single queue, so a transaction never
 * interleaves with another request's statements on the shared connection.
 */
class Database {
  constructor(raw) {
    this.raw = raw;
    this.queue = Promise.resolve();
  }

  static open(filename) {
    return new Promise((resolve, reject) => {
      const raw = new sqlite3.Database(filename, (err) => (err ? reject(err) : resolve(new Database(raw))));
    });
  }

  run(sql, params = []) {
    return this.enqueue(() => this.execute('run', sql, params));
  }

  get(sql, params = []) {
    return this.enqueue(() => this.execute('get', sql, params));
  }

  all(sql, params = []) {
    return this.enqueue(() => this.execute('all', sql, params));
  }

  /**
   * Runs `work(tx)` inside BEGIN/COMMIT, rolling back if it throws.
   * `tx` exposes run/get/all that bypass the queue (the transaction owns it).
   */
  transaction(work) {
    return this.enqueue(async () => {
      await this.execute('run', 'BEGIN');
      const tx = {
        run: (sql, params = []) => this.execute('run', sql, params),
        get: (sql, params = []) => this.execute('get', sql, params),
        all: (sql, params = []) => this.execute('all', sql, params),
      };
      try {
        const result = await work(tx);
        await this.execute('run', 'COMMIT');
        return result;
      } catch (err) {
        await this.execute('run', 'ROLLBACK').catch(() => {});
        throw err;
      }
    });
  }

  enqueue(task) {
    const result = this.queue.then(task);
    this.queue = result.catch(() => {});
    return result;
  }

  execute(method, sql, params = []) {
    return new Promise((resolve, reject) => {
      if (method === 'run') {
        this.raw.run(sql, params, function onRun(err) {
          if (err) return reject(err);
          return resolve({ lastID: this.lastID, changes: this.changes });
        });
        return;
      }
      this.raw[method](sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
  }
}

module.exports = { Database };
