#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @brief    [UserManager] UserManager Class for managing user information during login process
# @author   Hyuk Jun Yoo (yoohj9475@kist.re.kr)
# @version  2_1    
# TEST 2024-06-05

from auth0.authentication import GetToken
from auth0.management import Auth0
from UserManager import auth0_config
import requests, json

def get_management_token():
    token_url = f"https://{auth0_config.AUTH0_DOMAIN}/oauth/token"
    headers = {'content-type': 'application/json'}
    payload = {
        'grant_type': 'client_credentials',
        'client_id': auth0_config.AUTH0_CLIENT_ID,
        'client_secret': auth0_config.AUTH0_CLIENT_SECRET,
        'audience': auth0_config.AUTH0_AUDIENCE
    }
    response = requests.post(token_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['access_token']

def authenticate_user(username, password):
    token_url = f"https://{auth0_config.AUTH0_DOMAIN}/oauth/token"
    headers = {'content-type': 'application/json'}
    payload = {
        'grant_type': 'http://auth0.com/oauth/grant-type/password-realm',
        'client_id': auth0_config.AUTH0_CLIENT_ID,
        'client_secret': auth0_config.AUTH0_CLIENT_SECRET,
        'username': username,
        'password': password,
        'realm': auth0_config.AUTH0_CONNECTION,
        'scope': 'openid'
    }
    response = requests.post(token_url, headers=headers, json=payload)
    if response.status_code == 200:
        return True
        # return response.json()
    else:
        return False
        # return None
    
def get_users(mgmt_api_token):
    users_url = f"https://{auth0_config.AUTH0_DOMAIN}/api/v2/users"
    headers = {
        'authorization': f'Bearer {mgmt_api_token}',
        'content-type': 'application/json'
    }
    response = requests.get(users_url, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    username = "kny@kist.re.kr"
    password = "123123kk!"
    user_info = authenticate_user(username, password)
    
    if user_info:
        print("Authentication successful!")
        print("User info:", json.dumps(user_info, indent=2))

        # Get management API token and fetch user list
        mgmt_api_token = get_management_token()
        users = get_users(mgmt_api_token)
        print("Users in the system:", json.dumps(users, indent=2))
    else:
        print("Authentication failed. Please check your username and password.")

if __name__ == "__main__":
    main()