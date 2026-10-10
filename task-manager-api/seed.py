"""Script para popular o banco com dados iniciais.

A senha dos usuários de exemplo vem da variável de ambiente SEED_USER_PASSWORD (obrigatória,
no mínimo 4 caracteres): nenhuma senha fica no código.
"""
import os
import sys
from datetime import timedelta

from app import create_app
from database import db
from models.category import Category
from models.clock import utc_now
from models.constants import PASSWORD_MIN_LENGTH
from models.task import Task
from models.user import User


def seed_data():
    password = os.environ.get('SEED_USER_PASSWORD', '')
    if len(password) < PASSWORD_MIN_LENGTH:
        sys.exit(f'SEED_USER_PASSWORD must be set (at least {PASSWORD_MIN_LENGTH} characters)')

    app = create_app()
    with app.app_context():

        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        users = []
        for name, email, role in (('João Silva', 'joao@email.com', 'admin'),
                                  ('Maria Santos', 'maria@email.com', 'user'),
                                  ('Pedro Oliveira', 'pedro@email.com', 'manager')):
            user = User()
            user.name = name
            user.email = email
            user.set_password(password)
            user.role = role
            db.session.add(user)
            users.append(user)
        u1, u2, u3 = users

        db.session.commit()

        categories = []
        for name, description, color in (('Backend', 'Tarefas de backend', '#3498db'),
                                         ('Frontend', 'Tarefas de frontend', '#2ecc71'),
                                         ('DevOps', 'Tarefas de infraestrutura', '#e74c3c'),
                                         ('Bug', 'Correção de bugs', '#e67e22')):
            category = Category()
            category.name = name
            category.description = description
            category.color = color
            db.session.add(category)
            categories.append(category)
        c1, c2, c3, c4 = categories

        db.session.commit()

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


if __name__ == '__main__':
    seed_data()
