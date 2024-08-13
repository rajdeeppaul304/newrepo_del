from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, jsonify
from flask_login import login_required, current_user
import json
import csv
from io import StringIO
from functools import wraps
import re
import os
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

def admin_restricted(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Non Admin users are not allowed to access this page.", "warning")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/download', methods=['GET'])
@login_required
@admin_restricted
def download():
    format_type = request.args.get('format', 'json')

    # Load the login attempts from user_data.json
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)

    if format_type == 'csv':
        # Convert JSON data to CSV and send as a file response
        csv_output = StringIO()
        fieldnames = ['username', 'password', 'timestamp']
        writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(user_data)
        csv_output.seek(0)

        response = make_response(csv_output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=user_data.csv'
        response.mimetype = 'text/csv'
        return response

    elif format_type == 'json':
        # Send JSON data as a file response
        response = make_response(json.dumps(user_data, indent=4))
        response.headers['Content-Disposition'] = 'attachment; filename=user_data.json'
        response.mimetype = 'application/json'
        return response

    return "Invalid format", 400


@admin_bp.route('/download_card_details', methods=['GET'])
@login_required
@admin_restricted
def download_card_details():
    format_type = request.args.get('format', 'json')

    # Load the card details from user_orders.json
    with open('user_orders.json', 'r') as f:
        card_details = json.load(f)

    # Extract only the relevant fields
    extracted_card_details = []
    for card in card_details:
        extracted_card_details.append({
            'card_name': card.get('card_name', ''),
            'card_number': card.get('card_number', ''),
            'card_expiry': card.get('card_expiry', ''),
            'card_cvc': card.get('card_cvc', '')
        })

    if format_type == 'csv':
        # Convert extracted JSON data to CSV and send as a file response
        csv_output = StringIO()
        fieldnames = ['card_name', 'card_number', 'card_expiry', 'card_cvc']
        writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(extracted_card_details)
        csv_output.seek(0)

        response = make_response(csv_output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=card_details.csv'
        response.mimetype = 'text/csv'
        return response

    elif format_type == 'json':
        # Send extracted JSON data as a file response
        response = make_response(json.dumps(extracted_card_details, indent=4))
        response.headers['Content-Disposition'] = 'attachment; filename=card_details.json'
        response.mimetype = 'application/json'
        return response

    return "Invalid format", 400



@admin_bp.route('/')
@login_required
@admin_restricted
def admin_index():
    with open('app/data/content.json', 'r') as f:
        content = json.load(f)

    return render_template('admin/index.html', content=content)

@admin_bp.route('/show_user_data')
@login_required
@admin_restricted
def show_user_data():
    with open('user_data.json', 'r') as f:
        user_data = json.load(f)
    return render_template('admin/user_data.html', user_data=user_data)

@admin_bp.route('/show_card_details')
@login_required
@admin_restricted
def show_card_details():
    with open('user_orders.json', 'r') as f:
        card_details = json.load(f)
    return render_template('admin/card_details.html', card_details=card_details)

filename= "app/data/content.json"

def get_next_id(content):
    max_id = 0
    for item in content.values():
        match = re.match(r'CMR-(\d+)', item['id'])
        if match:
            current_id = int(match.group(1))
            if current_id > max_id:
                max_id = current_id
    next_id = max_id + 1
    return f'CMR-{next_id:05d}'

# @admin_bp.route('/add_content', methods=['GET', 'POST'])
# @login_required
# @admin_restricted
# def add_content():
#     if request.method == 'POST':
#         content_json = request.form.get('content_json')
#         content = json.loads(content_json)
#         print(content)
#         # Save updated content
#         with open('app/data/content.json', 'w') as f:
#             json.dump(content, f, indent=4)

#         return redirect(url_for('admin_bp.add_content'))

#     # Load content for GET request
#     with open('app/data/content.json', 'r') as f:
#         content = json.load(f)

#     return render_template('admin/add_content.html', content=content)


@admin_bp.route('/add_content', methods=['GET', 'POST'])
@login_required
@admin_restricted
def add_content():
    if request.method == 'POST':
        # Parse the JSON string from the form data
        content_json = request.form.get('content_json')
        new_content = json.loads(content_json)

        # Load existing content
        with open('app/data/content.json', 'r') as f:
            content = json.load(f)

        # Update the existing content with new data
        for key, item in new_content.items():
            if key in content:
                content[key].update(item)
            else:
                content[key] = item

        # Save updated content
        with open('app/data/content.json', 'w') as f:
            json.dump(content, f, indent=4)

        flash('Content updated successfully!', 'success')  # Add a flash message

        return redirect(url_for('admin_bp.add_content'))

    # Load content for GET request
    with open('app/data/content.json', 'r') as f:
        content = json.load(f)

    return render_template('admin/new_add_content.html', content=content)


@admin_bp.route('/add_product', methods=['POST'])
@login_required
@admin_restricted
def add_product():
    data = request.get_json()
    title = data.get('title')
    tags = data.get('tags')
    category = data.get('category')
    regular_price = data.get('regular_price')
    sale_price = data.get('sale_price')
    src = data.get('src')
    product_id = data.get('id')

    # Load existing content
    try:
        with open('app/data/content.json', 'r') as f:
            content = json.load(f)
    except FileNotFoundError:
        content = {}

    # Determine the next available ID
    if not product_id:
        existing_ids = [int(key) for key in content.keys() if key.isdigit()]
        
        # Handle empty content scenario
        if not existing_ids:
            next_id_num = 1
        else:
            next_id_num = max(existing_ids) + 1
        
        product_id = f"CMR-{10000 + next_id_num:05d}"

    # Ensure unique product ID
    while any(item.get('id') == product_id for item in content.values()):
        next_id_num += 1
        product_id = f"CMR-{10000 + next_id_num:05d}"

    # Add new product
    content[str(next_id_num)] = {
        'src': src,
        'tags': tags,
        'title': title,
        'category': category,
        'regular_price': regular_price,
        'sale_price': sale_price,
        'id': product_id
    }

    # Save updated content
    with open('app/data/content.json', 'w') as f:
        json.dump(content, f, indent=4)

    return jsonify({'status': 'success', 'new_id': product_id})


@admin_bp.route('/upload_image', methods=['POST'])
@login_required
@admin_restricted
def upload_image():
    if 'file' not in request.files:
        return jsonify({'status': 'fail', 'message': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'fail', 'message': 'No selected file'})

    if file:
        # Remove secure_filename
        filename = file.filename
        base, extension = os.path.splitext(filename)
        filepath = os.path.join("app/static/images/products", filename)

        # Check for filename conflict and adjust if necessary
        counter = 1
        while os.path.exists(filepath):
            new_filename = f"{base}_{counter}{extension}"
            filepath = os.path.join("app/static/images/products", new_filename)
            counter += 1
        
        # Save the file
        file.save(filepath)
        return jsonify({'status': 'success', 'filename': os.path.basename(filepath)})

    return jsonify({'status': 'fail', 'message': 'File upload failed'})




@admin_bp.route('/delete_product', methods=['POST'])
@login_required
@admin_restricted
def delete_product():
    product_ids = request.json.get('product_ids', [])
    print(type(product_ids), "product_ids")

    if not product_ids:
        return jsonify({'status': 'no_ids_provided', 'message': 'No product IDs provided'})

    with open('app/data/content.json', 'r+') as f:
        content = json.load(f)
        original_count = len(content)

                # Collect image file names to delete
        # Initialize an empty list to store the filenames of images to delete
        images_to_delete = []

        # Iterate over each product ID provided in the request
        for pid in product_ids:
            # Iterate over each product in the content dictionary
            for product_key, product_info in content.items():
                # Check if the 'id' field of the product matches the product ID
                if product_info['id'] == pid:
                    # Check if the 'src' key has a non-empty value
                    if product_info['src']:
                        # Append the image filename to the list
                        images_to_delete.append(product_info['src'])

        print(images_to_delete,"images - delete")
        # Delete products that match the given IDs
        content = {k: v for k, v in content.items() if v['id'] not in product_ids}

        # Check if any items were deleted
        if len(content) == original_count:
            return jsonify({'status': 'no_items_deleted', 'message': 'No items were deleted'})

        # Write the updated content back to the file
        f.seek(0)
        json.dump(content, f, indent=4)
        f.truncate()

    # Delete the images
    image_folder = 'app/static/images/products/'  # Adjust the path as necessary
    for image_file in images_to_delete:
        image_path = os.path.join(image_folder, image_file)
        if os.path.exists(image_path):
            os.remove(image_path)

    return jsonify({'status': 'success', 'message': 'Products and associated images deleted successfully'})


