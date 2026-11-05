'use strict';

// Amounts are stored and summed as integer cents (exact); clients still receive decimal numbers.
const CENTS_PER_UNIT = 100;

const toCents = (amount) => Math.round(amount * CENTS_PER_UNIT);
const fromCents = (cents) => cents / CENTS_PER_UNIT;

module.exports = { toCents, fromCents };
