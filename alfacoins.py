import requests
import hashlib
import json
import random
import string

import config


def hash_password():
    md5pass = hashlib.md5(config.ALFACOINS_PASSWORD.encode('utf-8')).hexdigest().upper()
    return md5pass


def id_generator():
    chars = string.ascii_letters + string.digits
    size = 22
    return ''.join(random.choice(chars) for x in range(size))


def create_order(order_id):
    password = hash_password()
    payment_url = 'https://www.alfacoins.com/api/create'
    order_data = {
        'name': config.ALFACOINS_NAME,
        'secret_key': config.ALFACOINS_SECRETKEY,
        'password': password,
        'type': 'litecointestnet',
        'amount': 1,
        'order_id': order_id,
        'currency': 'USD',
        'description': 'Payment for new EOS account',
        'options': {
                    'notificationURL': config.NOTIFICATION_URL,
                    'redirectURL': config.REDIRECT_URL,
                    'payerName': 'vztest',
                    'payerEmail': 'vztest@test.io'
                    }
    }
    response = requests.post(payment_url, json=order_data)
    response_output = response.json()
    return response_output


def get_order_status(order_id):
    status_url = 'https://www.alfacoins.com/api/status'
    password = hash_password()
    order_data = {
        'name': config.ALFACOINS_NAME,
        'secret_key': config.ALFACOINS_SECRETKEY,
        'password': password,
        'txn_id': order_id
    }
    response = requests.post(status_url, json=order_data)
    response_output = response.json()
    return response_output['status']
