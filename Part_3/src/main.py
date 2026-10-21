from di.container import container
from database import db
from flask_jwt_extended import JWTManager


def main():
    app = container.app
    
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    main()