# -*- coding: utf-8 -*-
"""
@Description:
@Date       : 2024/8/22 1:48
@Author     : lkkings
@FileName:  : 导入钱包.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import json
from solders.keypair import Keypair
from solders.pubkey import Pubkey

with open('dev-wallet-data-02.json', mode='r', encoding='utf-8') as f:
    wallet = json.load(f)

public_key = Pubkey.from_string(wallet['public_key'])
keypair = Keypair.from_bytes(wallet['secret_key'])
print(keypair.pubkey() == public_key)
