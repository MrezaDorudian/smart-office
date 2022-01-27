import json
from datetime import datetime
import random
import jwt
import requests


def authenticate(user_id, password):
    with open('localServerDatabase.json', 'r') as f:
        database = json.load(f)
        for key, value in database['users'].items():
            if value['username'] == user_id:
                if value['password'] == password:
                    return True
        return False


def get_random_number_by_time():
    current_hour = datetime.now().strftime("%H:%M:%S").split(':')[0]
    current_hour = int(current_hour)
    if 8 <= current_hour <= 16:
        random_number = str(random.randint(66, 100))
    elif 20 <= current_hour <= 24 or 0 <= current_hour <= 4:
        random_number = str(random.randint(0, 33))
    else:
        random_number = str(random.randint(33, 66))
    return random_number


def send_get_request_to_central_server(user_id, office_id, jwt_secret_key, type_of_request):
    print('Authentication successful')
    token = jwt.encode({'from': 'local_server', 'user_id': f'{user_id}', 'office_id': f'{office_id}', 'type': type_of_request}, jwt_secret_key)
    response = requests.get('http://localhost:8888', headers={'Authorization': f'Bearer {token}'})
    light = response.text.strip().replace('"', '')
    random_number = get_random_number_by_time()
    if int(light) > int(random_number):
        return_value = int(light) - int(random_number)
    else:
        return_value = 0
    return return_value
