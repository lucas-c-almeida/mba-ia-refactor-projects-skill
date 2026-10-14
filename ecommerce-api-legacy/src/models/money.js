'use strict';

const CENTS_PER_UNIT = 100;

/** Money is stored and summed as integer cents; clients still receive a decimal number. */
function centsToAmount(cents) {
  return cents / CENTS_PER_UNIT;
}

module.exports = { centsToAmount };
