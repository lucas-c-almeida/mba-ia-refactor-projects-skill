"""Script para popular o banco com dados iniciais.

Seed passwords are never committed (AP-01): they come from SEED_ADMIN_PASSWORD,
SEED_USER_PASSWORD and SEED_MANAGER_PASSWORD, or are generated at random and printed once.
"""
import os
import secrets
from datetime import timedelta

from app import create_app
from database import db
from models.category import Category
from models.clock import utc_now
from models.task import (STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING,
                         Task)
from models.user import ROLE_ADMIN, ROLE_MANAGER, ROLE_USER, User

GENERATED_PASSWORD_BYTES = 12


def _seed_password(variable):
    value = os.environ.get(variable)
    if value:
        return value, False
    return secrets.token_urlsafe(GENERATED_PASSWORD_BYTES), True


def _user(name, email, role, password_variable, generated):
    password, was_generated = _seed_password(password_variable)
    if was_generated:
        generated.append((email, password))
    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role
    db.session.add(user)
    return user


def _category(name, description, color):
    category = Category()
    category.name = name
    category.description = description
    category.color = color
    db.session.add(category)
    return category


def seed_data():
    app = create_app()
    generated = []
    with app.app_context():
        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        u1 = _user('João Silva', 'joao@email.com', ROLE_ADMIN, 'SEED_ADMIN_PASSWORD', generated)
        u2 = _user('Maria Santos', 'maria@email.com', ROLE_USER, 'SEED_USER_PASSWORD', generated)
        u3 = _user('Pedro Oliveira', 'pedro@email.com', ROLE_MANAGER, 'SEED_MANAGER_PASSWORD',
                   generated)
        db.session.commit()

        c1 = _category('Backend', 'Tarefas de backend', '#3498db')
        c2 = _category('Frontend', 'Tarefas de frontend', '#2ecc71')
        c3 = _category('DevOps', 'Tarefas de infraestrutura', '#e74c3c')
        c4 = _category('Bug', 'Correção de bugs', '#e67e22')
        db.session.commit()

        now = utc_now()
        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': STATUS_PENDING, 'priority': 1, 'user_id': u1.id, 'category_id': c1.id, 'due_date': now - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': STATUS_IN_PROGRESS, 'priority': 2, 'user_id': u2.id, 'category_id': c2.id, 'due_date': now + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': STATUS_DONE, 'priority': 2, 'user_id': u3.id, 'category_id': c3.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': STATUS_PENDING, 'priority': 1, 'user_id': u1.id, 'category_id': c4.id, 'due_date': now - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': STATUS_PENDING, 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'due_date': now + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': STATUS_PENDING, 'priority': 2, 'user_id': u2.id, 'category_id': c1.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': STATUS_CANCELLED, 'priority': 4, 'user_id': u3.id, 'category_id': c1.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': STATUS_IN_PROGRESS, 'priority': 3, 'user_id': u2.id, 'category_id': c1.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': STATUS_PENDING, 'priority': 4, 'user_id': u3.id, 'category_id': c3.id, 'due_date': now + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': STATUS_PENDING, 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'tags': 'improvement,validation'},
        ]

        for td in tasks_data:
            t = Task()
            t.title = td['title']
            t.description = td['description']
            t.status = td['status']
            t.priority = td['priority']
            t.user_id = td['user_id']
            t.category_id = td['category_id']
            if 'due_date' in td:
                t.due_date = td['due_date']
            if 'tags' in td:
                t.tags = td['tags']
            db.session.add(t)

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")
        for email, password in generated:
            print(f"  senha gerada para {email}: {password}")


if __name__ == '__main__':
    seed_data()
