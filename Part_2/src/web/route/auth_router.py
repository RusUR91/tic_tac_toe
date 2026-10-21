from flask import request, jsonify
from web.model.signup_request import SignUpRequest
from web.auth.user_authenticator import public_endpoint, require_auth

def register_auth_routes(app, user_service, user_authenticator):
    
    @app.post('/auth/register')
    @public_endpoint
    def register():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing JSON body'}), 400
            
            login = data.get('login')
            password = data.get('password')
            
            if not login or not password:
                return jsonify({'error': 'Login and password are required'}), 400
            
            signup_request = SignUpRequest(login, password)
            user_service.register(signup_request)
            
            return jsonify({'message': 'User registered successfully'}), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.post('/auth/login')
    @public_endpoint
    def login():
        try:
            user_uuid = user_authenticator.authenticate()
            return jsonify({'uuid': user_uuid}), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500