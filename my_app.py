from app import app

if __name__ == '__main__':
    app.run()
# waitress-serve --port=8080 wsgi:app