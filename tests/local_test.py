import eosfactory.eosf as eosf
import eosfactory
import sys, os
import json
import argparse
import subprocess
import string
import time
import numpy as np
import pandas as pd
pd.set_option('display.width', 500)
pd.set_option('display.max_rows',10)
pd.set_option('display.float_format', '{:.3f}'.format)
#pd.options.display.float_format = '${:,.2f}'.format

############# Must also modify in boidtoken.hpp ##############
# TESTING Speeds Only
WEEK_WAIT    = 7 # seconds

################################# Test variables #########################################

#NUM_ACCOUNTS        = 100
NUM_ACCOUNTS        = 10
TEST_DURATION       = [1,8,10,20]*WEEK_WAIT
MAX_BOID_SUPPLY     = 1e12
INIT_BOIDTOKENS     = np.linspace(1,10e9,NUM_ACCOUNTS)
INIT_BOIDPOWER      = np.linspace(0,10e3,NUM_ACCOUNTS)
INIT_BOIDSTAKE      = INIT_BOIDTOKENS/10


##############################################################

BOID_TOKEN_CONTRACT_PATH = \
     os.path.abspath(
         os.path.join(
             os.path.dirname(os.path.abspath(__file__)),
             '..'))

##########################################################################################
digs = string.digits + string.ascii_letters
def eos_name_digits(x):
    if x < 0:
        sign = -1
    elif x == 0:
        return digs[0 + 1]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(digs[int(x % 5) + 1])
        x = int(x / 5)

    if sign < 0:
        digits.append('-')

    digits.reverse()

    return ''.join(digits)

##########################################################################################

# @param account  The account to set/delete a permission authority for
# @param permission  The permission name to set/delete an authority for
# @param authority  NULL, public key, JSON string, or filename defining the authority
# @param parent  The permission name of this parents permission (Defaults to "active")
def setAccountPermission(account, permission, authority, parent, json=False, code=False):
    if json: json = '--json'
    else: json = ''
    if code: code = '--add-code'
    else: code = ''
    permissionCmd =\
        'cleos set account permission {0} {1} {2} {3} -p {0}@active {4}'.format(
                        account, permission, authority, parent, json)
    subprocess.call(permissionCmd, shell=True)

# @param account  The account to set/delete a permission authority for
# @param contract  The account that owns the code for the action
# @param actionName  The type of the action
# @param permissionName  The permission name required for executing the given action 
def setActionPermission(account, contract, actionName, permissionName):
    permissionCmd = \
            'cleos set action permission {0} {1} {2} {3} -p {0}@active'.format(
                        account, contract, actionName, permissionName)
    subprocess.call(permissionCmd, shell=True)

transferPermission = lambda x,y:\
   '\'{{\
        "threshold": 1,\
        "keys": [\
            {{\
                "key" : "{0}",\
                "weight" : 1\
            }}\
        ],\
        "accounts": [\
            {{\
                "permission": {{"actor": "{1}", "permission": "eosio.code"}},\
                "weight" : 1\
            }}\
        ]\
    }}\''.format(x,y)

def stake(acct, amount, memo):
    boidToken_c.push_action(
        'stake',
        {
            '_stake_account': acct,
            '_staked': amount,
            'memo': memo
        }, permission=[acct]
    )

def claim(acct):
    boidToken_c.push_action(
        'claim',
        {
            '_stake_account': acct
        }, permission = [boid_token] #, forceUnique=1)
    )

def unstake(acct, acct_permission, memo):
    boidToken_c.push_action(
        'unstake',
        {
            '_stake_account': acct,
            'memo': memo
        }, permission=[acct_permission]
    )

def initStaking():
    # initstats - reset/setup configuration of contract
    boidToken_c.push_action(
        'initstats',
        '{}', [boid_token])
    stakebreak('1')

def stakebreak(on_switch):
    boidToken_c.push_action(  # stakebreak - activate/deactivate staking for users
        'stakebreak',
        {
            'on_switch': on_switch
        }, [boid_token])

def setBoidpower(acct, bp):
    boidToken_c.push_action(
        'setnewbp',
        {
            'acct': acct,
            'boidpower': bp
        }, [boid_token, acct])

def setAutostake(acct, on_switch):
    boidToken_c.push_action(
        'setautostake',
        {
            '_stake_account': acct,
            'on_switch': on_switch 
        }, [acct])

def getBalance(x):
    if len(x.json['rows']) > 0:
        return float(x.json['rows'][0]['balance'].split()[0])
    else:
        return 0

def getStakeParams(x):
    ret = {}
    for i in range(len(x.json['rows'])):
        ret[x.json['rows'][i]['stake_account']] = \
            {
             'auto_stake': x.json['rows'][i]['auto_stake'],
             'staked': x.json['rows'][i]['staked']
            }
    return ret

def getBoidpowers(x):
    ret = {}
    for i in range(len(x.json['rows'])):
        ret[x.json['rows'][i]['acct']] = x.json['rows'][i]['quantity']
    return ret

def get_state(contract, contract_owner, accts, dfs, p=False):

    stake_params = getStakeParams(contract.table('stakes',contract_owner))
    bps = getBoidpowers(contract.table('boidpowers', contract_owner))
    for account_num, acct in enumerate(accts):
        account = 'account%d' % (account_num + 1)
        acct_balance = getBalance(contract.table("accounts", acct))
        staked_tokens = float(stake_params[account]['staked'].split()[0]) \
            if account in stake_params.keys() else 0.0
        acct_bp = float(bps[account]) if account in bps.keys() else 0.0
        print(account_num)
        dfs[account_num] = dfs[account_num].append({
            'boid_power': acct_bp,
            'staked_boid_tokens': staked_tokens,
            'unstaked_boid_tokens': acct_balance - staked_tokens,
            'total_boid_tokens': acct_balance
        }, ignore_index=True)

        if p: print('%s_balance = %f' % (acct, acct_balance))
        if p: print('stake params %s' % stake_params)
        if p: print('%s_bp = %f' % (acct, acct_bp))

    return dfs

def get_stake_roi(dfs):
    for df in dfs:
        stake_revenue = df['unstaked_boid_tokens'] - df['unstaked_boid_tokens'][0]
        df['stake_ROI'] = \
            100 * (stake_revenue / df['staked_boid_tokens'][0])
    return dfs

def get_total_roi(dfs):
    for df in dfs:
        df['total_ROI'] = \
            100 * (df['total_boid_tokens'] / df['total_boid_tokens'][0] - 1.0)
    return dfs

def print_acct_dfs(dfs):

    for i, (df, stake_period) in enumerate(zip(dfs, STAKE_PERIOD_STRINGS)):
        df.index.name = 'week'
        print('------------------------------------ acct%d ---- 1 %s stake -----------------------------------' % ((i + 1), stake_period))
        print(df)
        print('---------------------------------------------------------------------------------------------------')



if __name__ == '__main__':

    # determine if we want to
    # save the test data to a csv
    # build the contracts
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s","--save",
        action="store_true",
        help="save test data to csv file in ./results")
    parser.add_argument(
        "-b","--build",
        action="store_true",
        help="build new contract ABIs")
    args = parser.parse_args()

    # start single-node local testnet
    eosf.reset()

    # create master account from which
    # other account can be created
    # accessed via global variable: master
    w = eosf.wallet.Wallet()
    eosf.create_master_account('master')

    # Create contract owner account: boid_token
    eosf.create_account('boid_token', master, account_name='boid.token')

    accts = []
    for i in range(NUM_ACCOUNTS):
        eosf.create_account(
            'acct{}'.format(i),
            master,
            account_name='account{}'.format(eos_name_digits(i))
        )
        accts.append(eval('acct{}'.format(i)))

    # data frames to hold account state
    acct_df_columns = [
        'boid_power',
        'staked_boid_tokens',
        'unstaked_boid_tokens',
        'total_boid_tokens']

    # make build directory if it does not exist
    build_dir = os.path.join(BOID_TOKEN_CONTRACT_PATH, 'build')
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)

    # create reference to the token staking contract
    # build and deploy the contracts on the testnet
    boidToken_c = eosf.Contract(boid_token, BOID_TOKEN_CONTRACT_PATH)
    if args.build:
        boidToken_c.build()
    boidToken_c.deploy()


    ############# now we can call functions ##############
    ########## (aka actions) from the contract! ##########


    # Set up boid_token account as issuer of BOID
    boidToken_c.push_action(
        'create',
        {
            'issuer': boid_token,
            'maximum_supply': '{:.4f} BOID'.format(MAX_BOID_SUPPLY)
        }, [boid_token])

    # issue tokens to accts
    for i in range(NUM_ACCOUNTS):
        boidToken_c.push_action(
            'issue',
            {
                'to': accts[i],
                'quantity': '%.4f BOID' % INIT_BOIDTOKENS[i],
                'memo': 'memo'
            }, [boid_token])
        setBoidpower(accts[i], INIT_BOIDPOWER[i])

#    # test setters
#    boidToken_c.push_action('setmonth', {'month_stake_roi':'1.2'}, [boid_token])
#    boidToken_c.push_action('setbpratio', {'bp_bonus_ratio':'0.0002'}, [boid_token])
#    boidToken_c.push_action('setbpmult', {'bp_bonus_multiplier':'0.000002'}, [boid_token])
#    boidToken_c.push_action('setbpmax', {'bp_bonus_max':'55000.0'}, [boid_token])
#    boidToken_c.push_action('setminstake', {'min_stake':'5000.0'}, [boid_token])

    # TEST: Stake less than minimum amount
    try:
        initStaking()
        stake(accts[0], '%.4f BOID' % INIT_BOIDSTAKE[0], 'memo')
    except eosfactory.core.errors.Error as e:
        print(e)

    # TEST: Stake 1 account, valid amount, no boidpower
    dfs = [pd.DataFrame(columns=acct_df_columns)]
    stake(accts[1], '%.4f BOID' % INIT_BOIDSTAKE[1], 'memo')
    setBoidpower(accts[1], 0)
    setAutostake(accts[1], 0)
    stakebreak(0)
    # run test over time
    dfs = get_state(boidToken_c, boid_token, [accts[1]], dfs, True)
    for t in range(TEST_DURATION[0]):
        time.sleep(WEEK_WAIT)
        print('\n/-------------------- week %d --------------------------------\\' % (t+1))
        claim(accts[1])
        dfs = get_state(boidToken_c, boid_token, [accts[1]], dfs, True)
        print('\\--------------------- week %d ---------------------------------/' % (t+1))
    dfs = get_stake_roi(dfs)
    dfs = get_total_roi(dfs)

    unstake(accts[1], boid_token, 'memo')

    # end season
    stakebreak('1')

    # TEST: Stake multiple accounts, no boidpower
    dfs = []
    for i in range(len(accts)-1):
        stake(accts[i+1], '%.4f BOID' % INIT_BOIDSTAKE[i+1], 'memo')
        setBoidpower(accts[i+1], 0)
        setAutostake(accts[i+1], 0)
        dfs.append(pd.DataFrame(columns=acct_df_columns))

    stakebreak(0)
    # run test over time
    dfs = get_state(boidToken_c, boid_token, accts[1:], dfs)
    for t in range(TEST_DURATION[0]):
        time.sleep(WEEK_WAIT)
        print('\n/-------------------- week %d --------------------------------\\' % (t+1))
        for i in range(len(accts)-1):
            claim(accts[i+1])
            dfs = get_state(boidToken_c, boid_token, [accts[i+1]], dfs)
        print('\\--------------------- week %d ---------------------------------/' % (t+1))
    dfs = get_stake_roi(dfs)
    dfs = get_total_roi(dfs)

    for i in range(len(accts)-1):
        unstake(accts[i+1], boid_token, 'memo')

    # end season
    stakebreak('1')

    # TEST: Stake 1 account, high boidpower

    # TEST: Stake 1 account, low boidpower

    # TEST: Stake multiple accounts, varying boidpower

    # TEST: 1 account with all available BOID

    # TEST: Multiple accounts where BOID supply is gone

    # TEST: Attempt stake during bonus period

    # TEST: Attempt unstake during bonus period

    # TEST: Attempt unstake during stake break

    # TEST: Stake 1 account with varying boidpower

    # TEST: Claim early

    # TEST: Claim late

    # TEST: Attempt transfer staked tokens


    '''
    # stake boid tokens
    stake(acct1, '%.4f BOID' % INIT_BOIDSTAKE, "memo")
    boidToken_c.push_action(
        'setautostake',
        {
            '_stake_account': acct1,
            'on_switch': '1'
        }, [acct1])
    
    stake(acct2, '%.4f BOID' % INIT_BOIDSTAKE, "memo1")
    unstake(acct2, acct2, "memo1")
    stake(acct2, '%.4f BOID' % INIT_BOIDSTAKE, "memo2")
    unstake(acct2, acct2, "memo2")
    stake(acct2, '%.4f BOID' % INIT_BOIDSTAKE, "memo3")

    stakebreak('0')  # disable staking, stakebreak is over


#     # run test over time
#     dfs = get_state(boidToken_c, boid_token, accts, dfs)
#     for t in range(TEST_DURATION):
# #        if t+1 > 1:  # testing exit
# #            eosf.stop()
# #            sys.exit()
#         time.sleep(WEEK_WAIT)
#         print('\n/-------------------- week %d --------------------------------\\' % (t+1))
#         for i, acct in enumerate(accts):
#             print('acct %d' % (i+1))
#             claim(acct)
#         dfs = get_state(boidToken_c, boid_token, accts, dfs)
#         print('\\--------------------- week %d ---------------------------------/' % (t+1))
#     dfs = get_stake_roi(dfs)
#     dfs = get_total_roi(dfs)

    # unstake the staked tokens of each account
    for acct in accts:
        unstake(acct, boid_token, "memo")

    # end season
    stakebreak('1')
    '''

    # # output test results, and save them to csv files if prompted
    # print_acct_dfs(dfs)
    # if args.save:
    #     save_loc = os.path.join(
    #         BOID_TOKEN_CONTRACT_PATH,
    #         'tests',
    #         'results')
    #     for acct, df in zip(accts, dfs):
    #         file_loc = os.path.join(save_loc, acct.name + '_df')
    #         df.to_csv(file_loc)

    # stop the testnet and exit python
    eosf.stop()
    sys.exit()
