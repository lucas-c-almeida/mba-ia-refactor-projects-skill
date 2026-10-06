'use strict';

const sqlite3 = require('sqlite3');

// Promise wrapper over one sqlite3 connection. Persistence code only: no HTTP, no rules.
class Database {
    constructor(connection) {
        this.connection = connection;
        this.transactionQueue = Promise.resolve();
    }

    static open(file) {
        return new Promise((resolve, reject) => {
            const connection = new sqlite3.Database(file, (err) => {
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

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.connection.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }

    // Runs `work` inside BEGIN/COMMIT. Transactions are queued, because a single connection
    // cannot hold two of them at once and concurrent requests would otherwise interleave.
    transaction(work) {
        const result = this.transactionQueue.then(async () => {
            await this.run('BEGIN IMMEDIATE');
            try {
                const value = await work();
                await this.run('COMMIT');
                return value;
            } catch (err) {
                await this.run('ROLLBACK');
                throw err;
            }
        });
        this.transactionQueue = result.catch(() => undefined);
        return result;
    }
}

module.exports = { Database };
