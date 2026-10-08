const { asyncHandler } = require('../middlewares/asyncHandler');

// Delivery only: parse, call one controller method, render.
function checkoutRoutes(router, checkout) {
    router.post('/api/checkout', asyncHandler(async (req, res) => {
        const result = await checkout.checkout(req.body || {});
        res.status(200).json(result);
    }));
    return router;
}

module.exports = { checkoutRoutes };
