import os
import json
from werkzeug.security import check_password_hash
from flask_login import UserMixin
from app import login_manager

from flask_login import UserMixin
import json

class User(UserMixin):
    def __init__(self, user_id, username, password, is_admin=False):
        self.id = user_id
        self.username = username
        self.password = password
        self.is_admin = is_admin

    def get_id(self):
        return self.id

    def is_admin(self):
        return self.is_admin

def load_users_from_json():
    with open('user_info.json', 'r') as f:
        data = json.load(f)

    users = {}
    for user_id, user_data in data.get('user', {}).items():
        users[user_id] = User(user_id, user_data['username'], user_data['password'])
    
    # Add admin user manually
    if 'admin' in data:
        admin_data = data['admin']
        users['admin'] = User(admin_data['id'], admin_data['username'], admin_data['password'], is_admin=True)

    return users

users = load_users_from_json()


@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)
