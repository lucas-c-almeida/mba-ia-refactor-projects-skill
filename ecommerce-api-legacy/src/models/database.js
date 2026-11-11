// Connection to the datastore, with promise-based helpers over the sqlite3 callback API.
const sqlite3 = require('sqlite3');

function openDatabase(filename) {
    const raw = new sqlite3.Database(filename);

    const run = (sql, params = []) => new Promise((resolve, reject) => {
        raw.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });

    const get = (sql, params = []) => new Promise((resolve, reject) => {
        raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });

    const all = (sql, params = []) => new Promise((resolve, reject) => {
        raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });

    // One connection is shared by every request, so writes are queued: a transaction never
    // interleaves with another request's writes.
    let queue = Promise.resolve();
    function exclusive(work) {
        const result = queue.then(() => work());
        queue = result.catch(() => {});
        return result;
    }

    function transaction(work) {
        return exclusive(async () => {
            await run('BEGIN');
            try {
                const result = await work();
                await run('COMMIT');
                return result;
            } catch (err) {
                await run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
    }

    return { run, get, all, exclusive, transaction };
}

module.exports = { openDatabase };
