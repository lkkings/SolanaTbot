# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/3 22:32
@Author     : lkkings
@FileName:  : instructions.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.sysvar import INSTRUCTIONS
from spl.token.constants import TOKEN_PROGRAM_ID

from flashloan.solend.layouts import BORROW_LAYOUT, REPAY_LAYOUT


class LendingInstruction:
    FlashBorrowReserveLiquidity = 19
    FlashRepayReserveLiquidity = 20


def build_flash_borrow_instruction(liquidity_amount: int,
                                   source_liquidity: Pubkey,
                                   destination_liquidity: Pubkey,
                                   reserve: Pubkey,
                                   lending_market: Pubkey,
                                   lending_program_id: Pubkey
                                   ) -> Instruction:
    """
      创建一个用于闪电借贷的交易指令。

      :param liquidity_amount: 借款的流动资金量
      :param source_liquidity: 源流动性账户的公钥
      :param destination_liquidity: 目标流动性账户的公钥
      :param reserve: 储备账户的公钥
      :param lending_market: 借贷市场的公钥
      :param lending_program_id: 借贷程序的公钥
      :return: 返回一个 Solana 的交易指令
      """
    data = BORROW_LAYOUT.build(dict(
        instruction=LendingInstruction.FlashBorrowReserveLiquidity,
        liquidityAmount=liquidity_amount
    ))

    # Find the lending market authority
    lending_market_authority_seeds = [bytes(lending_market)]
    lending_market_authority, _ = Pubkey.find_program_address(
        seeds=lending_market_authority_seeds,
        program_id=lending_program_id
    )
    accounts = [
        AccountMeta(pubkey=source_liquidity, is_signer=False, is_writable=True),
        AccountMeta(pubkey=destination_liquidity, is_signer=False, is_writable=True),
        AccountMeta(pubkey=reserve, is_signer=False, is_writable=True),
        AccountMeta(pubkey=lending_market, is_signer=False, is_writable=False),
        AccountMeta(pubkey=lending_market_authority, is_signer=False, is_writable=False),
        AccountMeta(pubkey=INSTRUCTIONS, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False)
    ]
    return Instruction(
        program_id=lending_program_id,
        accounts=accounts,
        data=data
    )


def build_flash_repay_instruction(liquidity_amount,
                                  borrow_instruction_index,
                                  source_liquidity,
                                  destination_liquidity,
                                  reserve_liquidity_fee_receiver,
                                  host_fee_receiver,
                                  reserve,
                                  lending_market,
                                  user_transfer_authority,
                                  lending_program_id) -> Instruction:
    """
      创建一个用于还款的 Solana 交易指令。

      :param liquidity_amount: 需要还款的流动性数量
      :param borrow_instruction_index: 借款指令的索引
      :param source_liquidity: 源流动性账户的公钥
      :param destination_liquidity: 目标流动性账户的公钥
      :param reserve_liquidity_fee_receiver: 预留流动性费用接收者账户的公钥
      :param host_fee_receiver: 主机费用接收者账户的公钥
      :param reserve: 预留账户的公钥
      :param lending_market: 借贷市场的公钥
      :param user_transfer_authority: 用户转账授权账户的公钥
      :param lending_program_id: 借贷程序的公钥
      :return: 返回一个 Solana 的交易指令
      """
    data = REPAY_LAYOUT.build(dict(
        instruction=LendingInstruction.FlashRepayReserveLiquidity,
        liquidityAmount=liquidity_amount,
        borrowInstructionIndex=borrow_instruction_index,
    ))
    accounts = [
        AccountMeta(pubkey=source_liquidity, is_signer=False, is_writable=True),
        AccountMeta(pubkey=destination_liquidity, is_signer=False, is_writable=True),
        AccountMeta(pubkey=reserve_liquidity_fee_receiver, is_signer=False, is_writable=True),
        AccountMeta(pubkey=host_fee_receiver, is_signer=False, is_writable=True),
        AccountMeta(pubkey=reserve, is_signer=False, is_writable=False),
        AccountMeta(pubkey=lending_market, is_signer=False, is_writable=False),
        AccountMeta(pubkey=user_transfer_authority, is_signer=True, is_writable=False),
        AccountMeta(pubkey=INSTRUCTIONS, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False)
    ]
    return Instruction(
        program_id=lending_program_id,
        accounts=accounts,
        data=data
    )
