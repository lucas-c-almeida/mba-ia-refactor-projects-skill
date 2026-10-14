"""Script para popular o banco com dados iniciais.

A senha das contas de exemplo vem da variável de ambiente SEED_PASSWORD. Sem ela, uma senha
aleatória é gerada e exibida uma única vez.
"""
import os
import secrets
from datetime import timedelta

from sqlalchemy import delete, func, select

from app import create_app
from database import db
from models.category import Category
from models.clock import utc_now
from models.task import Task
from models.user import User

SEED_USERS = (
    ('João Silva', 'joao@email.com', 'admin'),
    ('Maria Santos', 'maria@email.com', 'user'),
    ('Pedro Oliveira', 'pedro@email.com', 'manager'),
)

SEED_CATEGORIES = (
    ('Backend', 'Tarefas de backend', '#3498db'),
    ('Frontend', 'Tarefas de frontend', '#2ecc71'),
    ('DevOps', 'Tarefas de infraestrutura', '#e74c3c'),
    ('Bug', 'Correção de bugs', '#e67e22'),
)


def _count(model):
    return db.session.scalar(select(func.count()).select_from(model))


def seed_data(app, password):
    with app.app_context():
        for model in (Task, User, Category):
            db.session.execute(delete(model))
        db.session.commit()

        users = []
        for name, email, role in SEED_USERS:
            user = User()
            user.name = name
            user.email = email
            user.set_password(password)
            user.role = role
            db.session.add(user)
            users.append(user)
        db.session.commit()

        categories = []
        for name, description, color in SEED_CATEGORIES:
            category = Category()
            category.name = name
            category.description = description
            category.color = color
            db.session.add(category)
            categories.append(category)
        db.session.commit()

        u1, u2, u3 = users
        c1, c2, c3, c4 = categories
        now = utc_now()
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

        for entry in tasks_data:
            task = Task()
            for field, value in entry.items():
                setattr(task, field, value)
            db.session.add(task)
        db.session.commit()

        print("Seed concluído com sucesso!")
        print(f"  {_count(User)} usuários")
        print(f"  {_count(Category)} categorias")
        print(f"  {_count(Task)} tasks")


if __name__ == '__main__':
    seed_password = os.environ.get('SEED_PASSWORD')
    if not seed_password:
        seed_password = secrets.token_urlsafe(12)
        print(f"SEED_PASSWORD não definida: senha gerada para as contas de exemplo: {seed_password}")
    seed_data(create_app(), seed_password)
