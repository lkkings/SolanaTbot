# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/8/24 21:58
@Author     : lkkings
@FileName:  : __init__.py.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import json
import os
from os import getenv
from pathlib import Path
from typing import List, Union, Dict, Tuple

from anchorpy import Wallet as AnchorWallet
from solana.rpc.types import TokenAccountOpts
from solana.transaction import Transaction
from solders.hash import Hash
from solders.instruction import Instruction, AccountMeta
from solders.keypair import Keypair
from solders.message import to_bytes_versioned, MessageV0
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams, ID as SYS_PROGRAM_ID
from solders.transaction import VersionedTransaction
from solders.sysvar import RENT
from spl.token.constants import TOKEN_PROGRAM_ID, ACCOUNT_LEN, ASSOCIATED_TOKEN_PROGRAM_ID
from spl.token.instructions import create_associated_token_account, get_associated_token_address, close_account, \
    CloseAccountParams

from clients.rpc import connection
from logger import catch_exceptions

TX = Union[Transaction, VersionedTransaction]


class Wallet(AnchorWallet):
    """Python wallet object."""

    def __init__(self, payer: Keypair):
        """Initialize the wallet.

        Args:
            payer: the Keypair used to sign transactions.
        """
        self._payer: Keypair = payer
        self._associated_token_accounts: Dict[str, Pubkey] = {}
        self._min_balance_rent_exempt_token_acc = 0

    @catch_exceptions(option='钱包初始化', retry=100)
    async def initialize(self):
        token_accounts_resp = await connection.get_token_accounts_by_owner_json_parsed(
            self.public_key, TokenAccountOpts(program_id=TOKEN_PROGRAM_ID)
        )
        for token_account in token_accounts_resp.value:
            mint = token_account.account.data.parsed['info']['mint']
            self._associated_token_accounts[mint] = token_account.pubkey

    async def get_balance(self) -> int:
        return (await connection.get_balance(self.public_key)).value

    def get_associated_token_account(self, mint: str):
        return self._associated_token_accounts.get(mint)

    def add_associated_token_account(self, mint: str, account: Pubkey):
        self._associated_token_accounts[mint] = account

    def remove_associated_token_account(self, mint: str):
        del self._associated_token_accounts[mint]

    def close_associated_token_account(self, mint: str) -> Instruction:
        return close_account(
            CloseAccountParams(account=Pubkey.from_string(mint), dest=self.public_key, owner=self.public_key,
                               program_id=TOKEN_PROGRAM_ID)
        )

    def create_associated_token_account(self, mint: str) -> Instruction:
        associated_token_address, _ = Pubkey.find_program_address(
            seeds=[bytes(self.public_key), bytes(TOKEN_PROGRAM_ID), bytes(Pubkey.from_string(mint))],
            program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
        )
        associated_token_instruction = Instruction(
            accounts=[
                AccountMeta(pubkey=self.payer.pubkey(), is_signer=True, is_writable=True),
                AccountMeta(pubkey=associated_token_address, is_signer=False, is_writable=True),
                AccountMeta(pubkey=self.payer.pubkey(), is_signer=False, is_writable=False),
                AccountMeta(pubkey=Pubkey.from_string(mint), is_signer=False, is_writable=False),
                AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
                AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
                AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
            ],
            program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
            data=bytes(0),
        )
        # associated_token_address, _ = Pubkey.find_program_address(
        #     seeds=[bytes(self.public_key), bytes(TOKEN_2022_PROGRAM_ID), bytes(mint)],
        #     program_id=ASSOCIATED_TOKEN_PROGRAM_ID,
        # )
        # token_account_instruction = create_associated_token_account(self.public_key, self.public_key, mint)
        self._associated_token_accounts[str(mint)] = associated_token_address
        return associated_token_instruction

    @property
    def public_key(self) -> Pubkey:
        """Get the public key of the wallet."""
        return self._payer.pubkey()

    @property
    def payer(self) -> Keypair:
        return self._payer

    def sign_transaction(self, tx: TX) -> TX:
        """Sign a transaction using the wallet's keypair.

        Args:
            tx: The transaction to sign.

        Returns:
            The signed transaction.
        """
        if isinstance(tx, VersionedTransaction):
            signature = self.payer.sign_message(to_bytes_versioned(tx.message))
            tx = VersionedTransaction.populate(tx.message, [signature])
        else:
            tx.sign(self.payer)
        return tx

    @classmethod
    def load(cls, wallet_json: Union[Path, str]) -> 'Wallet':
        with Path(wallet_json).open() as wallet_json:
            keypair: List[int] = json.load(wallet_json)
        return cls(Keypair.from_bytes(keypair))

    @classmethod
    def load_from_key(cls, private_key: str) -> 'Wallet':
        try:
            return cls(Keypair.from_base58_string(private_key))
        except:
            return cls(Keypair.from_base58_string(os.getenv('PRIVATE_KEY')))

    @classmethod
    def local(cls) -> 'Wallet':
        """Create a wallet instance from the filesystem.

        Uses the path at the ANCHOR_WALLET env var if set,
        otherwise uses ~/.config/solana/id.json.
        """
        try:
            return cls.load(getenv("ANCHOR_WALLET", Path.home() / ".config/solana/id.json"))
        except:
            return cls(Keypair.from_base58_string(os.getenv('PRIVATE_KEY')))

    @classmethod
    def dummy(cls) -> 'Wallet':
        """Create a dummy wallet instance that won't be used to sign transactions."""
        keypair = Keypair()
        return cls(keypair)

    def transfer(self, receiver: Union[Pubkey, str], lamports: int) -> Instruction:
        if isinstance(receiver, str):
            receiver = Pubkey.from_string(receiver)
        return transfer(TransferParams(
            from_pubkey=self.payer.pubkey(),
            to_pubkey=receiver,
            lamports=lamports)
        )
