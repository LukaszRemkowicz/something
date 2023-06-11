
# Concept
It's a requirement project, which core use case is to play at TIC TAC TOE. Written in clean architecture.
This is mostly a REST API project, but it has a frontend served by flask, operated by javascript too. 
Frontend is not a priority, but it's a nice to have, that's why there is not all the features implemented.

To play, you need firstly create a simple account:
```bash
POST localhost:8001/register
{
    "email": ,
    "password": 
}
```
Later on, you have to login:
```bash
POST localhost:8001/login
{
    "email": ,
    "password": 
}
```
Next, copy a jwt token from the response and paste it to the header of the request.
To start playing, you have to create a session:
```bash
GET localhost:8001/session
```
When session started, you can play:
```bash
POST localhost:8001/session/{session_id}/game/{game_id}
{
  "row": 1, 
  "col": 1
}
```
Game id is taken from session endpoint response.
To get a game status:
```bash
GET localhost:8001/session/{session_id}/game/{game_id}
```
If you are out of credits, you can add them to your account with condition: you have to have 0 in your account.
```bash
PATCH localhost:8001/account/update
```
If game finished, but session is still active, you can start a new game:
```bash
GET localhost:8001/session/{session_id}/game
```
If you want print high scores from today's date:
```bash
GET localhost:8001/high_scores
```
At last, you can check your account details:
```bash
GET localhost:8001/account
```

## configuration

Change the name of example.env to .env and fill it with your data.

# How to play?

docker:
```bash
docker-compose up --build
```
cmd/terminal:

```bash
pipenv install
pipenv shell
flask run --host 0.0.0.0 --port 8001 --reload --debug
```

### Tests

```bash
pipenv install --dev
pytest .
```
