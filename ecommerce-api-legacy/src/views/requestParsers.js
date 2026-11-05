'use strict';

const { ValidationError } = require('../models/errors');

// Boundary validation (RP-11): every value read from a request is checked for type and range
// here, before a controller sees it. A request that fails answers 400 "Bad Request" — the answer
// the application already gave to an incomplete checkout.

const DIGITS = /^\d+$/;

const isPlainObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const isNonEmptyString = (value) => typeof value === 'string' && value !== '';

/** An identifier: a safe integer, or a string of digits that is one. */
function parseId(value) {
  if (typeof value === 'number') return Number.isSafeInteger(value) ? value : null;
  if (typeof value === 'string' && DIGITS.test(value)) {
    const id = Number(value);
    return Number.isSafeInteger(id) ? id : null;
  }
  return null;
}

function parseCheckoutRequest(body) {
  if (!isPlainObject(body)) throw new ValidationError();
  const { usr, eml, pwd, c_id: courseIdInput, card } = body;

  // Presence first, exactly as the original checked it (a falsy value counts as absent).
  if (!usr || !eml || !courseIdInput || !card) throw new ValidationError();

  if (!isNonEmptyString(usr) || !isNonEmptyString(eml) || !isNonEmptyString(card)) {
    throw new ValidationError();
  }
  // The password is optional; a falsy value means "not given", as before.
  if (pwd && typeof pwd !== 'string') throw new ValidationError();

  const courseId = parseId(courseIdInput);
  if (courseId === null) throw new ValidationError();

  return { name: usr, email: eml, password: pwd || null, courseId, cardNumber: card };
}

function parseUserId(rawId) {
  const id = typeof rawId === 'string' ? parseId(rawId) : null;
  if (id === null) throw new ValidationError();
  return id;
}

module.exports = { parseCheckoutRequest, parseUserId };
