# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/24 14:49
@Author     : lkkings
@FileName:  : 获取所有代币余额.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import json

from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.system_program import create_account
from solana.rpc.types import TxOpts, TokenAccountOpts
from spl.token.constants import TOKEN_PROGRAM_ID

# 设置 Solana 客户端
solana_client = Client("https://api.devnet.solana.com")


def get_all_token_accounts(owner_pubkey: Pubkey):
    # 获取所有代币账户

    response = solana_client.get_token_accounts_by_owner_json_parsed(owner_pubkey,TokenAccountOpts(program_id=TOKEN_PROGRAM_ID))
    return response.value


def get_token_balance(token_account_pubkey: Pubkey):
    # 查询代币账户余额
    response = solana_client.get_token_account_balance(token_account_pubkey)
    return response.value.amount


def main():
    with open('../wallet-data/dev-wallet-02.json', mode='r', encoding='utf-8') as f:
        wallet = Keypair.from_bytes(json.load(f))
    token_accounts = get_all_token_accounts(wallet.pubkey())
    balance = solana_client.get_balance(wallet.pubkey())
    # 打印余额
    print(f"Balance: {balance.value}")
    # 打印所有代币账户及其余额
    for token_account_info in token_accounts:
        balance = get_token_balance(token_account_info.pubkey)
        print(f"Token Account: {token_account_info.pubkey}, Balance: {balance}")


if __name__ == "__main__":
    main()
