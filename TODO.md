

fix permissions bug:

	https://github.com/tokenika/eosfactory/issues/83
	summary:
		manually set permission with:
		cleos set account permission user1 active '{"threshold": 1,"keys": [{"key": "PRIVATE_KEY","weight": 1}],"accounts": [{"permission":{"actor":"contractB","permission":"eosio.code"},"weight":1}]}' owner -p user1

	http://eosfactory.io/build/html/cases/04_account/case.html
	summary:
		account_var_name.info()

		useful in proving what the permissions currently are

	https://github.com/EOSIO/eos/issues/4895
	summary:
		explaination of what the permissions should look like



Go to the file local_test.py in Token-Staking-Upgrade/tests/, starting on line 83 you'll see comments:

	Set up boid staking contract to boid.stake

	Set up boid power contract to boid.power

	Run staking tests with acct1 and acct2



Test staking with various different BOID quantities and with various stake/claim patterns



Run on testnet

