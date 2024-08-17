from app import app

if __name__ == '__main__':
    app.run(debug=True)
# waitress-serve --port=8080 wsgi:app