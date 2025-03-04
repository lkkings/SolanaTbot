# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/4 22:37
@Author     : lkkings
@FileName:  : utils.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import asyncio
import hashlib
from typing import List, Dict

from solders.pubkey import Pubkey
from spl.token._layouts import ACCOUNT_LAYOUT
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.core import AccountInfo as ParseAccountInfo

from clients.rpc import connection
from core.constants import MAX_SEED_LENGTH
from core.types.dex import AccountInfo, AccountInfoMap


def get_account_info(account_info_map: AccountInfoMap, account: Pubkey) -> AccountInfo:
    account_info = account_info_map.get(str(account))
    if account_info is None:
        raise Exception(f'账号{str(account)}信息缺失')
    return account_info


def generate_program_derived_address(seeds: list[bytes], additional_seed: Pubkey) -> Pubkey:
    combined_data = bytearray()

    # 拼接所有种子
    for seed in seeds:
        if len(seed) > MAX_SEED_LENGTH:
            raise ValueError("Max seed length exceeded")
        combined_data.extend(seed)

    # 拼接额外的种子和字符串 "ProgramDerivedAddress"
    combined_data.extend(bytes(additional_seed))
    combined_data.extend(b"ProgramDerivedAddress")

    # 计算SHA-256哈希
    sha256_hash = hashlib.sha256(combined_data).digest()

    # 创建并返回 PublicKey 对象
    return Pubkey(sha256_hash[:32])  # 取前32字节作为公钥


def to_array_like(number, length, byte_order='little'):
    """
    Convert an integer to a fixed-length byte array with specified byte order.

    :param number: The integer to convert.
    :param length: The length of the resulting byte array.
    :param byte_order: The byte order, 'little' for little-endian, 'big' for big-endian.
    :return: A byte array of the specified length.
    """
    # Convert the integer to a byte array
    byte_array = number.to_bytes(length, byte_order)

    # Ensure the byte array is exactly the specified length
    if len(byte_array) > length:
        byte_array = byte_array[-length:]
    elif len(byte_array) < length:
        byte_array = byte_array.rjust(length, b'\x00')

    return byte_array


def parse_token_account(account_info: AccountInfo) -> ParseAccountInfo:
    if not account_info:
        raise ValueError("Invalid account owner")

    if account_info.owner != TOKEN_PROGRAM_ID:
        raise AttributeError("Invalid account owner")

    bytes_data = account_info.data
    if len(bytes_data) != ACCOUNT_LAYOUT.sizeof():
        raise ValueError("Invalid account size")

    decoded_data = ACCOUNT_LAYOUT.parse(bytes_data)

    mint = Pubkey(decoded_data.mint)
    owner = Pubkey(decoded_data.owner)
    amount = decoded_data.amount

    if decoded_data.delegate_option == 0:
        delegate = None
        delegated_amount = 0
    else:
        delegate = Pubkey(decoded_data.delegate)
        delegated_amount = decoded_data.delegated_amount

    is_initialized = decoded_data.state != 0
    is_frozen = decoded_data.state == 2

    if decoded_data.is_native_option == 1:
        rent_exempt_reserve = decoded_data.is_native
        is_native = True
    else:
        rent_exempt_reserve = None
        is_native = False

    if decoded_data.close_authority_option == 0:
        close_authority = None
    else:
        close_authority = Pubkey(decoded_data.owner)

    return ParseAccountInfo(
        mint,
        owner,
        amount,
        delegate,
        delegated_amount,
        is_initialized,
        is_frozen,
        is_native,
        rent_exempt_reserve,
        close_authority,
    )
