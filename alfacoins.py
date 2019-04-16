import requests
import hashlib
import json
import random
import string

# md5pass = hashlib.md5("12!@qwQW".encode('utf-8')).hexdigest().upper()

# url = 'https://www.alfacoins.com/api/status'

# headers = {'Content-type': 'application/json',  # Определение типа данных
#            'Accept': 'text/plain',
#            'Content-Encoding': 'utf-8'}

# data = {
#   'name': 'vz invest',
#   'secret_key': '639fef4e4f6cb774900f777cde3c29af',
#   'password': md5pass,
#   'txn_id': 409081
# }

# response = requests.post(url, json=data)

# print(response.text)

# def create_order()

def hash_password():
    md5pass = hashlib.md5("12!@qwQW".encode('utf-8')).hexdigest().upper()
    return md5pass


def id_generator():
    chars = string.ascii_letters + string.digits
    size = 22
    return ''.join(random.choice(chars) for x in range(size))


def create_order(order_id):
    password = hash_password()
    payment_url = 'https://www.alfacoins.com/api/create'
    order_data = {
        'name': 'vz invest',
        'secret_key': '639fef4e4f6cb774900f777cde3c29af',
        'password': password,
        'type': 'litecointestnet',
        'amount': 1,
        'order_id': order_id,
        'currency': 'USD',
        'description': 'Payment for new EOS account',
        'options': {
                    'notificationURL': 'http://vzbj.ru/notification',
                    'redirectURL': 'http://vzbj.ru/processing',
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
        'name': 'vz invest',
        'secret_key': '639fef4e4f6cb774900f777cde3c29af',
        'password': password,
        'txn_id': order_id
    }
    response = requests.post(status_url, json=order_data)
    response_output = response.json()
    return response_output['status']
