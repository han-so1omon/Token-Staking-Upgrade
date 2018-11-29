

What does require_auth(_self) do?
	contracts inherit eosio::contract
	eosio::contract constructor is:
		contract(account_name n):_self(n) {}
	so _self is set to n, and n is the account that created the contract.

	require_auth(account_name n) - verifies that n is the account that is executing the action require_auth is in.
source: https://eosio.stackexchange.com/questions/1569/what-does-require-auth-self-do-in-eos


Very useful tool to navegate EOSFactory:
http://eosfactory.io/build/html/search.html?q=


Understanding Accounts and Permissions
	Accounts - human readable identifiers on the blockchain
		accounts have 2 named permissions:
			owner
				symbolizes ownership of the account. used for transactions that make changes to ownership, or recover other permissions that may have been compromised
			active
				authority to transfer funds, vote for block producers, and other high level account changes
		developers can also make custom permissions
		an account is required to make trasactions on the EOS blockchain
	Wallets - store keys associated with account(s)
		wallets have a locked and unlocked state and require a password to unlock
		eos repo comes with cleos that interfaces with kleos, which does this
		cleos:
			located at: ... tbd
			usage: used to interface with REST API exposed by nodeos and interact with the blockchain
		kleos:
			located at: eos/build/programs/keosd
			usage: used to store private keys
	Every permission has a parent permission. Parent permissions have the authority to change any of the permissions of their children
	Permissions have a weight and a threshhold. In a multi-sig, acount the weights of all the sigs permissions must equal or surpass the threshhold to do the action.
source: https://developers.eos.io/eosio-nodeos/docs/accounts-and-permissions
Questions:
	whats a named permission vs just a permission?
	where does keosd store the private keys?
	so is keosd a wallet, or software to create wallets?
	whats a rest api
	what is an example where the owner permission needs to be used to recover a compromised permission?
	what are the other high level account changes the active permission is used for?
	whats an example of a parent permission?
	HOW CAN I:
		LIST ALL THE KEY PAIRS ASSOCIATED WITH AN ACCOUNT?
		VIEW WHAT EACH KEY PAIR HAS PERMISSION TO DO?
		MODIFY PERMISSIONS OF AN ACCOUNT?

What are Active and Owner keys?
	An account has keys associated with it. All accounts have an owner key pair and an active key pair by default, but you can add more key pairs.
	Each key pair has the ability (aka permission) to do specified things. The owner key pair is like the root permission and can do anything. Active key pair can send transactions, etc. You could make another custom key pair that can only trade RAM. and if you gave that key pair to someone else they could trade RAM on your account but not transfer money, or anything of the sort.
source: https://www.reddit.com/r/eos/comments/8xce8z/what_are_active_and_owner_keys/
