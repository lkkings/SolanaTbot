# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/26 21:31
@Author     : lkkings
@FileName:  : lookup_table_provider.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import time
from typing import Dict, Set, List

from solders.address_lookup_table_account import AddressLookupTableAccount, AddressLookupTable
from solders.instruction import Instruction
from solders.pubkey import Pubkey

from clients.rpc import connection
from core.types.dex import AccountInfo

from logger import logger, catch_exceptions


class LookupTableProvider:
    def __init__(self):
        self.lookup_tables: Dict[str, AddressLookupTableAccount] = {}
        self.lookup_tables_for_address: Dict[str, Set[str]] = {}
        self.addresses_for_lookup_table = {}

    async def initialize(self):
        await lookup_table_provider.get_lookup_table(
            Pubkey.from_string('Gr8rXuDwE2Vd2F5tifkPyMaUR67636YgrZEjkJf9RR9V')
        )

    def update_cache(self, lut_address: Pubkey, lut_account: AddressLookupTableAccount):
        self.lookup_tables[str(lut_address)] = lut_account
        self.addresses_for_lookup_table[str(lut_address)] = set()

        for address in lut_account.addresses:
            address_str = str(address)
            self.addresses_for_lookup_table[str(lut_address)].add(address_str)
            if address_str not in self.lookup_tables_for_address:
                self.lookup_tables_for_address[address_str] = set()
            self.lookup_tables_for_address[address_str].add(str(lut_address))

    def process_lookup_table_update(self, lut_address: Pubkey, data: AccountInfo):
        lut_account = AddressLookupTableAccount(
            key=lut_address,
            addresses=AddressLookupTableAccount.from_bytes(data.data).addresses
        )
        self.update_cache(lut_address, lut_account)

    @catch_exceptions(option='批量更新路由表')
    async def batch_update(self, lut_addresses: List[Pubkey]):
        lut_addresses = [i for i in lut_addresses if i not in self.lookup_tables]
        if len(lut_addresses) == 0:
            return
        lut_addresses_str = [str(i) for i in lut_addresses]
        lut_accounts_map = await connection.get_accounts_info(lut_addresses_str)
        for lut_address_str, lut_account in lut_accounts_map.items():
            lut_address = Pubkey.from_string(lut_address_str)
            lut = AddressLookupTableAccount(
                key=lut_address,
                addresses=AddressLookupTable.deserialize(lut_account.data).addresses
            )
            self.update_cache(lut_address, lut)

    @catch_exceptions(option='获取路由表', retry=10)
    async def get_lookup_table(self, lut_address: Pubkey):
        lut_address_str = str(lut_address)
        if lut_address_str in self.lookup_tables:
            return self.lookup_tables[lut_address_str]

        lut_account_resp = await connection.get_account_info(lut_address)
        lut_account = lut_account_resp.value
        if lut_account is None:
            return None
        lut = AddressLookupTableAccount(
            key=lut_address,
            addresses=AddressLookupTable.deserialize(lut_account.data).addresses
        )
        self.update_cache(lut_address, lut)
        return lut

    def compute_ideal_lookup_tables_for_instructions(self, instructions: List[Instruction]):
        addresses = []
        for instruction in instructions:
            addresses.extend([i.pubkey for i in instruction.accounts])
        return lookup_table_provider.compute_ideal_lookup_tables_for_addresses(addresses)

    def compute_ideal_lookup_tables_for_addresses(self, addresses):
        MIN_ADDRESSES_TO_INCLUDE_TABLE = 2
        MAX_TABLE_COUNT = 3

        start_calc = time.time()

        address_set: Set[str] = set()
        table_intersections: Dict[str, int] = {}
        selected_tables: List[AddressLookupTableAccount] = []
        remaining_addresses: Set[str] = set()
        num_addresses_taken_care_of = 0

        for address in addresses:
            address_str = str(address)
            if address_str in address_set:
                continue
            address_set.add(address_str)

            tables_for_address = self.lookup_tables_for_address.get(address_str, set())
            if len(tables_for_address) == 0:
                continue

            remaining_addresses.add(address_str)
            for table in tables_for_address:
                table_intersections[table] = table_intersections.get(table, 0) + 1

        sorted_intersection_array = sorted(table_intersections.items(), key=lambda x: x[1], reverse=True)

        for lut_key, intersection_size in sorted_intersection_array:
            if intersection_size < MIN_ADDRESSES_TO_INCLUDE_TABLE or len(selected_tables) >= MAX_TABLE_COUNT or len(
                    remaining_addresses) <= 1:
                break

            lut_addresses = self.addresses_for_lookup_table.get(lut_key)

            address_matches = {x for x in remaining_addresses if x in lut_addresses}

            if len(address_matches) >= MIN_ADDRESSES_TO_INCLUDE_TABLE:
                selected_tables.append(self.lookup_tables[lut_key])
                for address in address_matches:
                    remaining_addresses.remove(address)
                    num_addresses_taken_care_of += 1

        logger.info(
            f"Reduced {len(address_set)} different addresses to {len(selected_tables)} lookup tables from "
            f"{len(sorted_intersection_array)} ({len(self.lookup_tables)}) candidates, with "
            f"{len(address_set) - num_addresses_taken_care_of} missing addresses in "
            f"{(time.time() - start_calc) * 1000:.2f}ms."
        )

        return selected_tables


lookup_table_provider = LookupTableProvider()
