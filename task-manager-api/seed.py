"""Script para popular o banco com dados iniciais"""
import os
import secrets
from datetime import timedelta

from app import create_app
from database import db
from models.category import Category
from models.clock import utc_now
from models.task import Task
from models.user import User

GENERATED_PASSWORD_BYTES = 9

SEED_USERS = (
    # (key, name, email, role, environment variable holding the password)
    ('admin', 'João Silva', 'joao@email.com', 'admin', 'SEED_ADMIN_PASSWORD'),
    ('member', 'Maria Santos', 'maria@email.com', 'user', 'SEED_USER_PASSWORD'),
    ('manager', 'Pedro Oliveira', 'pedro@email.com', 'manager', 'SEED_MANAGER_PASSWORD'),
)

SEED_CATEGORIES = (
    # (key, name, description, color)
    ('backend', 'Backend', 'Tarefas de backend', '#3498db'),
    ('frontend', 'Frontend', 'Tarefas de frontend', '#2ecc71'),
    ('devops', 'DevOps', 'Tarefas de infraestrutura', '#e74c3c'),
    ('bug', 'Bug', 'Correção de bugs', '#e67e22'),
)


def _seed_password(env_name, email):
    """The password comes from the environment; otherwise a random one is generated and shown once."""
    password = os.environ.get(env_name)
    if password:
        return password
    password = secrets.token_urlsafe(GENERATED_PASSWORD_BYTES)
    print(f"  senha gerada para {email}: {password}  (defina {env_name} para escolher a sua)")
    return password


def _create_users():
    users = {}
    for key, name, email, role, password_variable in SEED_USERS:
        user = User()
        user.name = name
        user.email = email
        user.set_password(_seed_password(password_variable, email))
        user.role = role
        db.session.add(user)
        users[key] = user
    db.session.commit()
    return users


def _create_categories():
    categories = {}
    for key, name, description, color in SEED_CATEGORIES:
        category = Category()
        category.name = name
        category.description = description
        category.color = color
        db.session.add(category)
        categories[key] = category
    db.session.commit()
    return categories


def _task_rows(users, categories, now):
    admin, member, manager = users['admin'], users['member'], users['manager']
    backend, frontend = categories['backend'], categories['frontend']
    devops, bug = categories['devops'], categories['bug']
    return [
        {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': admin.id, 'category_id': backend.id, 'due_date': now - timedelta(days=3)},
        {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': member.id, 'category_id': frontend.id, 'due_date': now + timedelta(days=5)},
        {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': manager.id, 'category_id': devops.id, 'tags': 'devops,ci,github'},
        {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': admin.id, 'category_id': bug.id, 'due_date': now - timedelta(days=1)},
        {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': admin.id, 'category_id': backend.id, 'due_date': now + timedelta(days=10)},
        {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': member.id, 'category_id': backend.id},
        {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': manager.id, 'category_id': backend.id},
        {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': member.id, 'category_id': backend.id, 'tags': 'refactor,tech-debt'},
        {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': manager.id, 'category_id': devops.id, 'due_date': now + timedelta(days=20)},
        {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': admin.id, 'category_id': backend.id, 'tags': 'improvement,validation'},
    ]


def _create_tasks(rows):
    for row in rows:
        task = Task()
        task.title = row['title']
        task.description = row['description']
        task.status = row['status']
        task.priority = row['priority']
        task.user_id = row['user_id']
        task.category_id = row['category_id']
        if 'due_date' in row:
            task.due_date = row['due_date']
        if 'tags' in row:
            task.tags = row['tags']
        db.session.add(task)
    db.session.commit()


def seed_data():
    app = create_app()
    with app.app_context():

        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = _create_users()
        categories = _create_categories()
        _create_tasks(_task_rows(users, categories, utc_now()))

        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")


if __name__ == '__main__':
    seed_data()
