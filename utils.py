import execjs
from eospy.cleos import Cleos
import requests


def verification_pubkey(pubkey):
	verification = execjs.compile('''
			const ecc = require('eosjs-ecc');
			function check_pubkey(key){
				return ecc.isValidPublic(key);
			}
		''')

	return verification.call('check_pubkey', pubkey)


def create_eos_acc(account_name, activekey, ownerkey):
	ce = Cleos(url='https://jungle2.cryptolions.io:443')
	key = "5HtBa93q7G1KkSNTQRCaNXsyNgAeBU4CcfVTsDBQXbktWDUud59"
	response = ce.create_account('testtestbet1', key, account_name,
	activekey, ownerkey,
                         stake_net='0.1000 EOS',
                         stake_cpu='0.1000 EOS',
                         ramkb=4,
                         permission='active',
                         transfer=True, broadcast=True)
	
	return response['transaction_id']
	


def check_account_accessability(account_name):
	ce = Cleos(url='https://jungle2.cryptolions.io:443')
	try:
		response = ce.get_account(account_name)
		if response:
			return False
	except requests.exceptions.HTTPError:
		return True
