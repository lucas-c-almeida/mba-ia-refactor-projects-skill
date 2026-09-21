// Promise-based wrapper over the sqlite3 driver. (AP-06 -> RP-06, AP-09 -> RP-09)
// The connection is created by the composition root and injected; nothing opens its own.
const sqlite3 = require('sqlite3');

class Database {
    constructor(connection) {
        this.connection = connection;
        // Serializes write units: a single shared connection cannot hold two transactions at once.
        this.writeQueue = Promise.resolve();
    }

    static open(path) {
        return new Promise((resolve, reject) => {
            const connection = new sqlite3.Database(path, (err) => {
                if (err) reject(err);
                else resolve(new Database(connection));
            });
        });
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.run(sql, params, function onRun(err) {
                if (err) reject(err);
                else resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    // Runs `work` inside BEGIN/COMMIT, rolling back on any failure. Units run one at a time.
    transaction(work) {
        const unit = this.writeQueue.then(async () => {
            await this.run('BEGIN');
            try {
                const result = await work();
                await this.run('COMMIT');
                return result;
            } catch (err) {
                await this.run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        this.writeQueue = unit.catch(() => {}); // keep the queue alive after a failed unit
        return unit;
    }

    close() {
        return new Promise((resolve, reject) => {
            this.connection.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = { Database };
