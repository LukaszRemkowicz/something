from datetime import timedelta
from typing import Tuple

from flask import Flask, jsonify, Response, request
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from flask_api import status

from entities.models import db, User, UserSession
from entities.types import Managers
from repos.managers import managers
from serializers import UserSerializer, UserUpdateSerializer
from settings import get_db_url, settings

manager: Managers = managers

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
app.config['JWT_SECRET_KEY'] = settings.jwt_secret
db.init_app(app)

jwt = JWTManager(app)


@app.route('/register', methods=['POST'])
def register() -> Tuple[Response, int]:
    """
    Simple register view.
    Due to simplicity, we are not using any validation or password hashing.
    """
    data: dict = request.json
    email: str = data.get('email')
    password: str = data.get('password')
    user_obj: User | None = User.query.filter_by(email=email, password=password).first()
    if user_obj:
        return jsonify({'message': 'User already exists'}), status.HTTP_400_BAD_REQUEST

    User.create(email=email, password=password)
    return jsonify({'message': 'User created'}), status.HTTP_201_CREATED


@app.route('/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """Simple login view. Due to simplicity, we are not using any refresh tokens."""
    email: str = request.json.get('email')
    password: str = request.json.get('password')

    user: User = User.query.filter_by(email=email, password=password).first()

    if user:
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
        return jsonify({'access_token': access_token}), status.HTTP_200_OK

    return jsonify({'message': 'Invalid credentials'}), status.HTTP_401_UNAUTHORIZED


@app.route('/account', methods=['GET'])
@jwt_required()
def account_detail() -> Tuple[Response, int]:
    """Returns account details."""
    current_user_id: str = get_jwt_identity()
    user: User = User.query.filter_by(id=current_user_id).first()

    if user:
        serializer: UserSerializer = UserSerializer(instance=user)
        serializer.is_valid()
        return jsonify(serializer.data), status.HTTP_200_OK
    return jsonify({'message': 'User not found'}), status.HTTP_404_NOT_FOUND


@app.route('/account/update', methods=['PATCH'])
@jwt_required()
def account_update() -> Tuple[Response, int]:
    """Updates account details."""
    current_user_id: str = get_jwt_identity()
    user: User = User.query.filter_by(id=current_user_id).first()
    data: dict = request.json

    if user:
        if data.get('credits') and user.credits != 0:
            message: str = 'Invalid credits count. Should be 0 before updating'
            return jsonify({'message': message}), status.HTTP_400_BAD_REQUEST
        serializer: UserUpdateSerializer = UserUpdateSerializer(
            instance=user, data=request.json
        )
        if not serializer.is_valid():
            return jsonify(serializer.errors), status.HTTP_400_BAD_REQUEST
        serializer.save()

        return jsonify({"status": "account updated", **serializer.data}), status.HTTP_200_OK
    return jsonify({'message': 'User not found'}), status.HTTP_404_NOT_FOUND


@app.route('/game/start', methods=['GET'])
@jwt_required()
def game() -> Tuple[Response, int]:
    current_user_id: str = get_jwt_identity()
    user: User | None = manager.UserManager.filter(id=current_user_id)
    breakpoint()
    if user.credits < 3:
        return jsonify({'message': 'Not enough credits'}), status.HTTP_400_BAD_REQUEST

    user.credits -= 3
    user.save()

    session_instance: UserSession | None = manager.UserSessionManager().create(
        user_id=current_user_id
    )
    response_message: str = f'Game started, with session id: {session_instance.id}'
    return jsonify({'status': response_message}), status.HTTP_200_OK
