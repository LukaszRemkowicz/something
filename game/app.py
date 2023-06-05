from datetime import timedelta
from typing import Tuple

from flask import Flask, jsonify, Response, request
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from flask_api import status

from entities.entites import UserPydantic
from entities.models import db
from entities.types import SessionStatus
from repos.db_repo import UserDBRepo, UserSessionDBRepo, GameDBRepo
from settings import get_db_url, settings
from use_cases.use_case import UserUseCase

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_db_url()
app.config['JWT_SECRET_KEY'] = settings.jwt_secret
db.init_app(app)

jwt = JWTManager(app)

player = UserUseCase(
    db_repo=UserDBRepo,
    user_session_repo=UserSessionDBRepo,
    game_db_repo=GameDBRepo
)


@app.route('/register', methods=['POST'])
def register() -> Tuple[Response, int]:
    """
    Simple register view.
    Due to simplicity, we are not using any validation or password hashing.
    """
    response: str
    status_code: int
    response, status_code = player.create_or_400(player_data=request.json)
    return jsonify(response), status_code


@app.route('/login', methods=['POST'])
def login() -> Tuple[Response, int]:
    """
    Simple login view. Due to simplicity, we are not using any refresh tokens.
    Note that password is not hashed, so it is plain text.
    """
    user: UserPydantic | None = player.get_user(email=request.json.get('email'))

    if not user or not user.password == request.json.get('password'):
        message: str = "User doesn't exists or password do not match"
        return jsonify({'message': message}), status.HTTP_401_UNAUTHORIZED

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
    return jsonify({'access_token': access_token}), status.HTTP_200_OK


@app.route('/account', methods=['GET'])
@jwt_required()
def account_detail() -> Tuple[Response, int]:
    """Returns account details."""
    current_user_id: str = get_jwt_identity()
    user: UserPydantic | None = player.get_user(id=current_user_id)

    if user:
        user_data: dict = user.dict()
        user_data.pop('password')
        return jsonify(user_data), status.HTTP_200_OK
    return jsonify({'message': 'User not found'}), status.HTTP_404_NOT_FOUND


@app.route('/account/update', methods=['PATCH'])
@jwt_required()
def account_update() -> Tuple[Response, int]:
    """Updates account details."""
    current_user_id: int = get_jwt_identity()
    response: dict
    status_code: int
    response, status_code = player.update_user_account(user_id=current_user_id, **request.json)
    return jsonify(response), status_code


@app.route('/game/start', methods=['GET'])
@jwt_required()
def game() -> Tuple[Response, int]:
    """Starts game session and return session id."""
    current_user_id: int = get_jwt_identity()
    response: str
    status_code: int
    response, status_code = player.start_session(user_id=current_user_id)
    return jsonify(response), status_code


@app.route('/game/plays/<int:session_id>', methods=['GET', "POST"])
@jwt_required()
def play_start(session_id: int) -> Tuple[Response, int]:
    """Starts game session and return session id."""
    current_user_id: int = get_jwt_identity()
    response: str
    status_code: int

    session_status: SessionStatus = player.check_session_status(
        session_id=session_id, user_id=current_user_id
    )

    if not session_status.active:
        return jsonify(session_status.session_data), session_status.status_code

    if request.method == 'POST':
        response, status_code = player.lets_play_POST(session_id=session_id, user_id=current_user_id)
        return jsonify(response), status_code

    if request.method == 'GET':
        response, status_code = player.lets_play_GET(session_id=session_id, user_id=current_user_id)
        return jsonify(response), status_code
