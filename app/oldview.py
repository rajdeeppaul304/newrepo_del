from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user, login_manager, LoginManager
from app import app
import json
from flask_login import UserMixin
# from app import login_manager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 




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
    with open('user_info.json', 'r') as f:
        data = json.load(f)
    for user_data in data.get('user', {}).values():
        if user_data['id'] == user_id:
            return User(user_data['id'], user_data['username'], user_data['password'])
    if user_id == 'admin':
        admin_data = data.get('admin', {})
        if admin_data.get('id') == user_id:
            return User(user_id, admin_data['username'], admin_data['password'], is_admin=True)
    return None


# class User(UserMixin):
#     def __init__(self, user_id, username, password, is_admin=False):
#         self.id = user_id
#         self.username = username
#         self.password = password
#         self.is_admin = is_admin

#     def get_id(self):
#         return self.id
    
# @login_manager.user_loader
# def load_user(user_id):
#     with open('user_info.json', 'r') as f:
#         data = json.load(f)
#     for user_data in data.get('user', {}).values():
#         if user_data['id'] == user_id:
#             return User(user_data['id'], user_data['username'], user_data['password'])
#     if user_id == 'admin':
#         admin_data = data.get('admin', {})
#         if admin_data.get('id') == user_id:
#             return User(user_id, admin_data['username'], admin_data['password'], is_admin=True)
#     return None


def load_content():
    with open('app/data/content.json', 'r') as file:
        return json.load(file)

@app.route('/')
def index():
    content = load_content()
    products = [
        {'src': f"images/products/{item['src']}" , 'tags': item['tags']}
        for item in content.values()
    ]
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Login attempt - Username: {username}, Password: {password}")

        # Load user data
        with open('user_info.json', 'r') as f:
            data = json.load(f)

        user_found = False
        user_obj = None

        # Check for admin login
        if username == 'admin':
            admin_data = data.get('admin', {})
            if admin_data.get('username') == username and admin_data.get('password') == password:
                user_obj = User('admin', username, password, is_admin=True)
                print("Admin login successful")
                login_user(user_obj)
                next_page = request.args.get('next') or url_for('index')
                return redirect(next_page)
            else:
                flash('Invalid admin credentials', 'danger')
                return render_template('login.html')

        # Check for regular user login
        for user_data in data.get('user', {}).values():
            if user_data['username'] == username:
                if user_data['password'] == password:
                    user_obj = User(user_data['id'], username, password)
                    print(f"Regular user login successful - ID: {user_obj.id}")
                    login_user(user_obj)
                    user_found = True
                    next_page = request.args.get('next') or url_for('index')
                    return redirect(next_page)                   
                else:
                    flash('Incorrect password', 'danger')
                    return render_template('login.html')

        if not user_found:
            # User does not exist, flash error message and redirect to the registration page
            flash('User does not exist, please register', 'danger')
            return redirect(url_for('register'))

    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Registration attempt - Username: {username}, Password: {password}")

        # Load user data
        with open('user_info.json', 'r') as f:
            data = json.load(f)

        # Check if the username already exists
        for user_data in data.get('user', {}).values():
            if user_data['username'] == username:
                flash('Username already exists', 'danger')
                return render_template('register.html')

        # Create a new user
        user_id = str(max([int(uid) for uid in data.get('user', {}).keys()] or [0]) + 1)
        new_user = {
            'id': user_id,
            'username': username,
            'password': password
        }
        data.setdefault('user', {})[user_id] = new_user

        # Save the updated user information to the JSON file
        with open('user_info.json', 'w') as f:
            json.dump(data, f, indent=4)

        user_obj = User(user_id, username, password)
        login_user(user_obj)

        next_page = request.args.get('next') or url_for('index')
        print(f"Redirecting to: {next_page}")
        return redirect(next_page)

    return render_template('register.html')


# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('index'))
