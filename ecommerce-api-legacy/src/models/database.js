// Promise wrapper over one SQLite connection, with serialized transactions (AP-06, AP-09).
// The connection is created by the composition root and injected here; this module opens nothing.
//
// A single connection shares one transaction scope, so writes are queued behind a lock: a
// transaction never absorbs another request's statements, and two BEGINs never overlap.

class Database {
    constructor(connection) {
        this.connection = connection;
        this.queue = Promise.resolve();
    }

    static executor(connection) {
        return {
            run(sql, params = []) {
                return new Promise((resolve, reject) => {
                    connection.run(sql, params, function onRun(err) {
                        if (err) return reject(err);
                        resolve({ lastID: this.lastID, changes: this.changes });
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

    exclusive(work) {
        const result = this.queue.then(work);
        this.queue = result.catch(() => {}); // keep the queue alive after a failure
        return result;
    }

    get(sql, params) { return Database.executor(this.connection).get(sql, params); }

    all(sql, params) { return Database.executor(this.connection).all(sql, params); }

    run(sql, params) {
        return this.exclusive(() => Database.executor(this.connection).run(sql, params));
    }

    exec(sql) {
        return new Promise((resolve, reject) => {
            this.connection.exec(sql, (err) => (err ? reject(err) : resolve()));
        });
    }

    // Runs `work(tx)` inside BEGIN/COMMIT; any rejection rolls the whole unit back.
    transaction(work) {
        return this.exclusive(async () => {
            const tx = Database.executor(this.connection);
            await tx.run('BEGIN');
            try {
                const value = await work(tx);
                await tx.run('COMMIT');
                return value;
            } catch (err) {
                // Deliberate and narrow: ROLLBACK only fails when SQLite already aborted the
                // transaction itself. The original error is the one that matters, and it propagates.
                await tx.run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
    }
}

module.exports = { Database };
