from flask import Flask
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('config.Config')

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'

from app import views
from app.admin.views import admin_bp
app.register_blueprint(admin_bp)
# from app.models import users

# def load_user(user_id):
#     return users.get(user_id)