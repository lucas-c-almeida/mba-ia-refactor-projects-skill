// Boundary checks: is this a well-formed request? Values are checked as sent, never coerced.
const { ValidationError } = require('../models/errors');

const INTEGER_TEXT = /^-?\d+$/;

function isPlainObject(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
}

// An identifier: a safe integer, or a string of digits that is one.
function parseId(raw) {
    if (typeof raw === 'number') return Number.isSafeInteger(raw) ? raw : null;
    if (typeof raw === 'string' && INTEGER_TEXT.test(raw)) {
        const value = Number(raw);
        return Number.isSafeInteger(value) ? value : null;
    }
    return null;
}

// Checkout body. The presence rule is the original one (every field but `pwd` must be truthy);
// what is new is that a present value of the wrong type is rejected instead of reaching the code.
function parseCheckout(body) {
    if (!isPlainObject(body)) throw new ValidationError();
    const { usr, eml, pwd, c_id: rawCourseId, card } = body;

    if (!usr || !eml || !rawCourseId || !card) throw new ValidationError();
    if (typeof usr !== 'string' || typeof eml !== 'string' || typeof card !== 'string') {
        throw new ValidationError();
    }
    if (pwd && typeof pwd !== 'string') throw new ValidationError();

    const courseId = parseId(rawCourseId);
    if (courseId === null) throw new ValidationError();

    return { name: usr, email: eml, password: pwd || null, courseId, cardNumber: card };
}

function parseUserId(raw) {
    const id = parseId(raw);
    if (id === null) throw new ValidationError();
    return id;
}

module.exports = { parseCheckout, parseUserId };
