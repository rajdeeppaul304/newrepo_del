from werkzeug.security import generate_password_hash

# Generate a hashed password
hashed_password = generate_password_hash('abc')
print(hashed_password)