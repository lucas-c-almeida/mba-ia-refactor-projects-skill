// Express 4 does not forward rejected promises to the error boundary; this does.
const asyncHandler = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};

module.exports = { asyncHandler };
