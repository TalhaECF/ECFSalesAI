import requests
import time
import json
from decouple import config

def get_access_token():
    """
    Generate an access token using client credentials flow.
    """
    tenant_id = config("TENANT_ID")
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': config("CLIENT_ID"),
        'client_secret':config("CLIENT_SECRET"),
        'scope': 'https://graph.microsoft.com/.default',
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Unable to get access token \n Error: {response.text}")


# 1st step
def initiate_session_copilot():
    """Initiates a session with an agent on copilot Studio"""
    try:
        url = "https://directline.botframework.com/v3/directline/tokens/generate"
        direct_client_secret = config("DIRECT_CLIENT_SECRET")

        headers = {
            'Authorization': f'Bearer {direct_client_secret}'
        }

        response = requests.request("POST", url, headers=headers)
        response_json = response.json()
        if response.status_code == 200:
            conv_id = response_json["conversationId"]
            token = response_json["token"]
            expires_in_sec = response_json["expires_in"]

            return [conv_id, token, expires_in_sec], True
    except Exception as e:
        raise e



# 2nd step
def initiate_conversation(token):
    try:
        url = "https://directline.botframework.com/v3/directline/conversations"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        response = requests.request("POST", url, headers=headers)
        response_json = response.json()
        if response.status_code == 201:
            return True
        return False
    except Exception as e:
        raise e


# 3rd step
def send_user_msg(token, conv_id, message, entra_id_access_token):
    try:
        url = f"https://directline.botframework.com/v3/directline/conversations/{conv_id}/activities"
        headers = {
            'Authorization': f'Bearer {token}',
            "User.AccessToken":f'Bearer {entra_id_access_token}'
        }
        body = {
            "type": "message",
            "From": {"id": "user1"},
            "Activity": {"From": {"id": "user1"}},
            "text": f"{message}"
        }
        response = requests.request("POST", url, json=body, headers=headers)
        response_json = response.json()
        if response.status_code == 200:
            return True
        return False

    except Exception as e:
        raise e


# def get_response_from_bot(token, entra_id_access_token, conv_id):
#     try:
#         url = f"https://directline.botframework.com/v3/directline/conversations/{conv_id}/activities"
#         headers = {
#             'Authorization': f'Bearer {token}',
#             # "User.AccessToken": f'Bearer {entra_id_access_token}'
#         }
#         requests.request("GET", url, headers=headers)
#         time.sleep(4)
#         response = requests.request("GET", url, headers=headers)
#         time.sleep(3)
#         response = requests.request("GET", url, headers=headers)
#         time.sleep(3)
#         if response.status_code == 200:
#             time.sleep(2)
#             activities = response.json().get('activities', [])
#             print(len(activities))
#             print(json.dumps(activities))
#             if activities:
#                 bot_response = str(activities[-2]["text"])
#                 print(bot_response)
#                 return bot_response, True
#
#         return "", False
#     except Exception as e:
#         raise e


def get_response_from_bot(token, entra_id_access_token, conv_id):
    try:
        url = f"https://directline.botframework.com/v3/directline/conversations/{conv_id}/activities"
        headers = {
            'Authorization': f'Bearer {token}',
            # "User.AccessToken": f'Bearer {entra_id_access_token}'
        }

        attempts = 0

        while attempts < 10:
            print(attempts)
            response = requests.request("GET", url, headers=headers)
            time.sleep(3)  # Pause between requests
            if response.status_code == 200:
                activities = response.json().get('activities', [])
                if len(activities) == 9:
                    bot_response = str(activities[-2]["text"])
                    print(bot_response)
                    return bot_response, True
            attempts += 1

        # If the desired condition is not met within 10 attempts
        return "", False
    except Exception as e:
        raise e


def complete_process(message):
    try:
        response_list, success = initiate_session_copilot()
        conv_id, token, expires_in_sec = response_list[0], response_list[1], response_list[2]
        conv_started = initiate_conversation(token)
        entra_id_access_token = get_access_token()
        send_user_msg(token, conv_id, message, entra_id_access_token)
        time.sleep(3)
        bot_response, success = get_response_from_bot(token, entra_id_access_token, conv_id)
        return bot_response, True

    except Exception as e:
        return str(e), False
