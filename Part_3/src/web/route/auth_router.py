from flask import request, jsonify
from web.model.signup_request import SignUpRequest
from web.model.jwt_request import JwtRequest
from web.model.refresh_jwt_request import RefreshJwtRequest
from web.auth.user_authenticator import require_auth


def register_auth_routes(app, user_service, user_authenticator):
    
    @app.post('/auth/register')
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
    def login():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing JSON body'}), 400
            
            login = data.get('login')
            password = data.get('password')
            
            if not login or not password:
                return jsonify({'error': 'Login and password are required'}), 400
            
            jwt_request = JwtRequest(login, password)
            jwt_response = user_service.authenticate(jwt_request)
            
            return jsonify(jwt_response.to_dict()), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.post('/auth/refresh')
    def refresh_tokens():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing JSON body'}), 400
            
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return jsonify({'error': 'Refresh token is required'}), 400
            
            refresh_request = RefreshJwtRequest(refresh_token)
            jwt_response = user_service.refresh_tokens(refresh_request.refresh_token)
            
            return jsonify(jwt_response.to_dict()), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.post('/auth/refresh-access')
    def refresh_access_token():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Missing JSON body'}), 400
            
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return jsonify({'error': 'Refresh token is required'}), 400
            
            refresh_request = RefreshJwtRequest(refresh_token)
            jwt_response = user_service.refresh_access_token(refresh_request.refresh_token)
            
            return jsonify(jwt_response.to_dict()), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.get('/auth/me')
    @require_auth(user_authenticator)
    def get_current_user():
        try:
            user = user_authenticator.get_authenticated_user()
            return jsonify({
                'uuid': user.uuid,
                'login': user.login
            }), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 401