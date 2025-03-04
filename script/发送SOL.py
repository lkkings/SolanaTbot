# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/24 14:15
@Author     : lkkings
@FileName:  : 发送SOL.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import json

from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.instruction import Instruction
from solders.message import MessageV0, Message
from solders.system_program import TransferParams, transfer

client: Client = Client("https://api.testnet.solana.com")

with open('../wallet-data/test-wallet-01.json', mode='r', encoding='utf-8') as f:
    sender = Keypair.from_bytes(json.load(f))

with open('../wallet-data/test-wallet-02.json', mode='r', encoding='utf-8') as f:
    receiver = Keypair.from_bytes(json.load(f))

instructions = [transfer(TransferParams(
    from_pubkey=sender.pubkey(),
    to_pubkey=receiver.pubkey(),
    lamports=100_000_000)
)]


latest_blockhash = client.get_latest_blockhash().value.blockhash
message = MessageV0.try_compile(payer=sender.pubkey(),instructions=instructions, address_lookup_table_accounts=[],
    recent_blockhash=latest_blockhash)

transaction = VersionedTransaction(message=message, keypairs=[sender])
client.send_transaction(transaction)
