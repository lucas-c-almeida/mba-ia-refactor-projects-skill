const { DependencyError } = require('../errors');

class UserController {
    constructor({ users }) { this.users = users; }

    async remove(id) {
        try {
            await this.users.deleteById(id);
        } catch (err) {
            throw new DependencyError('Erro DB', err);
        }
    }
}

module.exports = { UserController };
