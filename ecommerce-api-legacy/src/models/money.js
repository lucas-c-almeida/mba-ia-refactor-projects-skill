'use strict';

/**
 * Exact-arithmetic money helpers — part of the AP-20 fix (original: src/AppManager.js:12-16,
 * `price REAL` / `amount REAL`, binary floating point for currency). Storage and arithmetic
 * use integer cents; the JSON boundary keeps presenting a decimal number, in the same type
 * and format the original always sent (see `05-refactoring-playbook.md` RP-19 and the
 * baseline shapes in reports/baseline.json), so this conversion is not observable.
 */

function toCents(decimal) {
  return Math.round(Number(decimal) * 100);
}

function fromCents(cents) {
  return Math.round(cents) / 100;
}

module.exports = { toCents, fromCents };
