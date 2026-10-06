"""Populate the database with initial data.

Account passwords are configuration, never source (AP-01): set SEED_ADMIN_PASSWORD,
SEED_USER_PASSWORD and SEED_MANAGER_PASSWORD (see .env.example). The script fails loudly when
one is missing.
"""
from datetime import timedelta

from app import create_app
from config.settings import load_seed_passwords
from database import db
from models.category import Category
from models.clock import utcnow
from models.task import Task
from models.user import ROLE_ADMIN, ROLE_MANAGER, ROLE_USER, User


def _user(name, email, role, password):
    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    return user


def _category(name, description, color):
    category = Category(name=name, description=description, color=color)
    db.session.add(category)
    return category


def seed_data():
    passwords = load_seed_passwords()
    app = create_app()
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        u1 = _user('João Silva', 'joao@email.com', ROLE_ADMIN, passwords.admin)
        u2 = _user('Maria Santos', 'maria@email.com', ROLE_USER, passwords.user)
        u3 = _user('Pedro Oliveira', 'pedro@email.com', ROLE_MANAGER, passwords.manager)
        db.session.commit()

        c1 = _category('Backend', 'Tarefas de backend', '#3498db')
        c2 = _category('Frontend', 'Tarefas de frontend', '#2ecc71')
        c3 = _category('DevOps', 'Tarefas de infraestrutura', '#e74c3c')
        c4 = _category('Bug', 'Correção de bugs', '#e67e22')
        db.session.commit()

        now = utcnow()
        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': u1.id, 'category_id': c1.id, 'due_date': now - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': u2.id, 'category_id': c2.id, 'due_date': now + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': u3.id, 'category_id': c3.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': u1.id, 'category_id': c4.id, 'due_date': now - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'due_date': now + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': u2.id, 'category_id': c1.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': u3.id, 'category_id': c1.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': u2.id, 'category_id': c1.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': u3.id, 'category_id': c3.id, 'due_date': now + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'tags': 'improvement,validation'},
        ]
        db.session.add_all(Task(**data) for data in tasks_data)
        db.session.commit()

        print('Seed concluído com sucesso!')
        print(f'  {User.count_all()} usuários')
        print(f'  {Category.count_all()} categorias')
        print(f'  {Task.count_all()} tasks')

        # Release the pooled connections before the process exits (AP-13).
        db.session.remove()
        db.engine.dispose()


if __name__ == '__main__':
    seed_data()
