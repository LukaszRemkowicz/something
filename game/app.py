from datetime import timedelta
from typing import Tuple, Optional

from flask import Flask, jsonify, Response, request, render_template
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity, decode_token
from flask_api import status
from flask_cors import CORS

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

CORS(app)


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
        return jsonify({'error': message}), status.HTTP_401_UNAUTHORIZED

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=100))
    return jsonify({'access_token': access_token}), status.HTTP_200_OK


@app.route('/account', methods=['GET'])
@jwt_required()
def account_detail() -> Tuple[Response, int]:
    """Returns account details."""
    current_user_id: str = get_jwt_identity()
    user: UserPydantic | None = player.get_user(id=current_user_id)

    if user:
        user_data: dict = user.dict(exclude={'password'})
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


@app.route('/session', methods=['GET'])
@jwt_required()
def session() -> Tuple[Response, int]:
    """Starts game session and return object id."""
    current_user_id: int = get_jwt_identity()
    response: str
    status_code: int
    response, status_code = player.start_session(user_id=current_user_id)
    return jsonify(response), status_code


@app.route('/session/<int:session_id>/game', methods=['GET'])
@jwt_required()
def new_game(session_id: int) -> Tuple[Response, int]:
    """Create new board for session. Return board id."""
    current_user_id: int = get_jwt_identity()
    response: str
    status_code: int
    response, status_code = player.create_new_game(user_id=current_user_id, session_id=session_id)
    return jsonify(response), status_code


@app.route('/session/<int:session_id>/game/<int:board_id>', methods=['GET', "POST"])
@jwt_required()
def play_start(session_id: int, board_id: int) -> Tuple[Response, int]:
    """Starts game session and return session id."""
    current_user_id: int = get_jwt_identity()
    response: str
    status_code: int
    data: Optional[dict]
    from werkzeug.exceptions import BadRequest
    try:
        data = request.json
    except BadRequest:
        data = None

    session_status: SessionStatus = player.check_session_status(
        session_id=session_id, user_id=current_user_id
    )
    if not session_status.active:
        return jsonify(session_status.session_data), session_status.status_code

    is_finished, winner = player.check_game_status(
        session_id=session_id,
        user_id=current_user_id,
        game_id=board_id
    )
    if is_finished:
        return jsonify(winner), status.HTTP_200_OK

    if request.method == 'POST' and data:

        response, status_code = player.lets_play_POST(
            session_id=session_id,
            user_id=current_user_id,
            data=data,
            game_id=board_id
        )
        # if status_code != status.HTTP_200_OK:
        #     return jsonify(response), status_code
        # response, status_code = player.random_move(session_id=session_id, user_id=current_user_id)
        # is_finished, winner = player.check_game_status(session_id=session_id, user_id=current_user_id)
        # # if is_finished:
        # #     return jsonify({'winner': winner}), status.HTTP_200_OK
        return jsonify(response), status_code

    if request.method == 'GET':
        response, status_code = player.lets_play_GET(
            session_id=session_id,
            user_id=current_user_id,
            game_id=board_id
        )
        return jsonify(response), status_code


@app.route('/high_scores', methods=['GET'])
def high_scores() -> Tuple[Response, int]:
    """Returns high scores."""
    response: str
    status_code: int
    response, status_code = player.get_high_scores()
    return jsonify(response), status_code


@app.route('/session_view/<int:session_id>/game/<int:board_id>', methods=['GET', "POST"])
def index(session_id, board_id):
    return render_template('index.html')


@app.route('/login_view')
def login_view():
    return render_template('login.html')


@app.route('/session_view')
def session_view():

    token = request.args.get('token')
    try:
        payload = decode_token(token, app.config['SECRET_KEY'])
        current_user = payload['sub']
    except:
        current_user = None

    if token and current_user:
        return render_template('session.html')
    return render_template('login.html')


