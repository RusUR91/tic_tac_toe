from flask import jsonify
from web.auth.user_authenticator import require_auth

def register_user_routes(app, user_service, user_authenticator):
    
    @app.get('/user/<uuid>')
    @require_auth(user_authenticator)
    def get_user_by_uuid(uuid):
        try:
            user = user_service.get_user_by_uuid(uuid)
            return jsonify({
                'uuid': user.uuid,
                'login': user.login
            }), 200
        except ValueError as e:
            return jsonify({'error': str(e)}), 404