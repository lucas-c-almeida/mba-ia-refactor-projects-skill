"""Populate the database with initial data (operator script; it resets every table).

Passwords never live in the source (RP-01). Each seeded account takes its password from the
environment variable named below; when the variable is unset or empty the account gets a random
password nobody knows, and signing in with it requires setting the variable and seeding again.
"""
import os
import secrets
from datetime import timedelta

from app import create_app
from database import db
from models.category import Category
from models.clock import utc_now
from models.task import Task
from models.user import ROLE_ADMIN, ROLE_MANAGER, ROLE_USER, User

RANDOM_PASSWORD_BYTES = 18

USERS = [
    {'name': 'João Silva', 'email': 'joao@email.com', 'role': ROLE_ADMIN,
     'password_env': 'SEED_ADMIN_PASSWORD'},
    {'name': 'Maria Santos', 'email': 'maria@email.com', 'role': ROLE_USER,
     'password_env': 'SEED_USER_PASSWORD'},
    {'name': 'Pedro Oliveira', 'email': 'pedro@email.com', 'role': ROLE_MANAGER,
     'password_env': 'SEED_MANAGER_PASSWORD'},
]

CATEGORIES = [
    {'name': 'Backend', 'description': 'Tarefas de backend', 'color': '#3498db'},
    {'name': 'Frontend', 'description': 'Tarefas de frontend', 'color': '#2ecc71'},
    {'name': 'DevOps', 'description': 'Tarefas de infraestrutura', 'color': '#e74c3c'},
    {'name': 'Bug', 'description': 'Correção de bugs', 'color': '#e67e22'},
]

# user / category are indexes into USERS / CATEGORIES; due_in_days is relative to now.
TASKS = [
    {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user': 0, 'category': 0, 'due_in_days': -3},
    {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user': 1, 'category': 1, 'due_in_days': 5},
    {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user': 2, 'category': 2, 'tags': 'devops,ci,github'},
    {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user': 0, 'category': 3, 'due_in_days': -1},
    {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user': 0, 'category': 0, 'due_in_days': 10},
    {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user': 1, 'category': 0},
    {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user': 2, 'category': 0},
    {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user': 1, 'category': 0, 'tags': 'refactor,tech-debt'},
    {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user': 2, 'category': 2, 'due_in_days': 20},
    {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user': 0, 'category': 0, 'tags': 'improvement,validation'},
]


def _password_from_env(variable):
    return (os.environ.get(variable) or '').strip() or secrets.token_urlsafe(RANDOM_PASSWORD_BYTES)


def seed_data(app):
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = []
        for spec in USERS:
            account = User(name=spec['name'], email=spec['email'], role=spec['role'])
            account.set_password(_password_from_env(spec['password_env']))
            db.session.add(account)
            users.append(account)
        db.session.commit()

        categories = [Category(**spec) for spec in CATEGORIES]
        db.session.add_all(categories)
        db.session.commit()

        now = utc_now()
        for spec in TASKS:
            item = Task(title=spec['title'], description=spec['description'],
                        status=spec['status'], priority=spec['priority'],
                        user_id=users[spec['user']].id,
                        category_id=categories[spec['category']].id)
            if 'due_in_days' in spec:
                item.due_date = now + timedelta(days=spec['due_in_days'])
            if 'tags' in spec:
                item.tags = spec['tags']
            db.session.add(item)
        db.session.commit()

        print("Seed concluído com sucesso!")
        print(f"  {User.count_all()} usuários")
        print(f"  {Category.count_all()} categorias")
        print(f"  {Task.count_all()} tasks")
        unset = [spec['password_env'] for spec in USERS if not os.environ.get(spec['password_env'])]
        if unset:
            print(f"  senha aleatória (desconhecida) para: {', '.join(unset)}")


if __name__ == '__main__':
    seed_data(create_app())
