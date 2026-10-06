'use strict';

// Money is stored and summed as integer cents (AP-20, RP-19); it crosses the HTTP boundary
// as the same decimal number clients always received.
const CENTS_PER_UNIT = 100;

const toCents = (amount) => Math.round(Number(amount) * CENTS_PER_UNIT);
const fromCents = (cents) => cents / CENTS_PER_UNIT;

module.exports = { toCents, fromCents };
