const sqlite3 = require('sqlite3');

// Thin promise wrapper over the sqlite3 driver. Receives nothing and has no import-time effects.
function openDatabase(filename = ':memory:') {
    const raw = new sqlite3.Database(filename);

    return {
        run(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.run(sql, params, function onRun(err) {
                    if (err) return reject(err);
                    return resolve({ lastID: this.lastID, changes: this.changes });
                });
            });
        },
        get(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
            });
        },
        all(sql, params = []) {
            return new Promise((resolve, reject) => {
                raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
            });
        },
    };
}

module.exports = { openDatabase };
