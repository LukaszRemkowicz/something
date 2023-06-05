import pytest
from flask import jsonify

from app import app

# def test_login_success(client):
#     data = jsonify({'username': 'example', 'password': 'password'})
#     response = client.post('/login', data)
#     assert response.status_code == 200
#     assert 'access_token' in response.json


# def test_login_failure(client):
#     # Send a POST request to the login endpoint with invalid credentials
#     response = client.post('/login', data={'username': 'invalid', 'password': 'invalid'})
#
#     # Assert that the response has a status code of 401 (Unauthorized)
#     assert response.status_code == 401
#
#     # Assert that the response contains the error message
#     assert response.json == {'message': 'Invalid credentials'}
#
# def test_login_endpoint(client):
#     # Define the request data
#     data = {'username': 'example', 'password': 'password'}
#
#     # Call the login endpoint directly, passing the request data
#     response = login(data)
#
#     # Assert that the response has a status code of 200 (OK)
#     assert response.status_code == 200
#
#     # Assert that the response contains the access token
#     assert 'access_token' in response.json
