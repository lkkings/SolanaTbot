# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/13 7:53
@Author     : lkkings
@FileName:  : event.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Union, Dict


class EventType(Enum):
    ANY = -1  #任何事件
    UNKNOWN = 0  # 未知类型
    NFT_BID = 1  # NFT 投标
    NFT_BID_CANCELLED = 2  # NFT 投标已取消
    NFT_LISTING = 3  # NFT 上架
    NFT_CANCEL_LISTING = 4  # NFT 取消上架
    NFT_SALE = 5  # NFT 销售
    NFT_MINT = 6  # NFT 铸造
    NFT_AUCTION_CREATED = 7  # NFT 拍卖创建
    NFT_AUCTION_UPDATED = 8  # NFT 拍卖更新
    NFT_AUCTION_CANCELLED = 9  # NFT 拍卖取消
    NFT_PARTICIPATION_REWARD = 10  # NFT 参与奖励
    NFT_MINT_REJECTED = 11  # NFT 铸造被拒绝
    CREATE_STORE = 12  # 创建商店
    WHITELIST_CREATOR = 13  # 白名单创建者
    ADD_TO_WHITELIST = 14  # 添加到白名单
    REMOVE_FROM_WHITELIST = 15  # 从白名单中移除
    AUCTION_MANAGER_CLAIM_BID = 16  # 拍卖经理认领投标
    EMPTY_PAYMENT_ACCOUNT = 17  # 付款账户为空
    UPDATE_PRIMARY_SALE_METADATA = 18  # 更新主要销售元数据
    ADD_TOKEN_TO_VAULT = 19  # 将代币添加到保险库
    ACTIVATE_VAULT = 20  # 激活保险库
    INIT_VAULT = 21  # 初始化保险库
    INIT_BANK = 22  # 初始化银行
    INIT_STAKE = 23  # 初始化质押
    MERGE_STAKE = 24  # 合并质押
    SPLIT_STAKE = 25  # 拆分质押
    SET_BANK_FLAGS = 26  # 设置银行标志
    SET_VAULT_LOCK = 27  # 设置保险库锁
    UPDATE_VAULT_OWNER = 28  # 更新保险库所有者
    UPDATE_BANK_MANAGER = 29  # 更新银行经理
    RECORD_RARITY_POINTS = 30  # 记录稀有度积分
    ADD_RARITIES_TO_BANK = 31  # 向银行添加稀有度
    INIT_FARM = 32  # 初始化农场
    INIT_FARMER = 33  # 初始化农民
    REFRESH_FARMER = 34  # 刷新农民
    UPDATE_FARM = 35  # 更新农场
    AUTHORIZE_FUNDER = 36  # 授权资助者
    DEAUTHORIZE_FUNDER = 37  # 取消授权资助者
    FUND_REWARD = 38  # 资助奖励
    CANCEL_REWARD = 39  # 取消奖励
    LOCK_REWARD = 40  # 锁定奖励
    PAYOUT = 41  # 支付
    VALIDATE_SAFETY_DEPOSIT_BOX_V2 = 42  # 验证安全存款箱 V2
    SET_AUTHORITY = 43  # 设置权限
    INIT_AUCTION_MANAGER_V2 = 44  # 初始化拍卖经理 V2
    UPDATE_EXTERNAL_PRICE_ACCOUNT = 45  # 更新外部价格账户
    AUCTION_HOUSE_CREATE = 46  # 拍卖行创建
    CLOSE_ESCROW_ACCOUNT = 47  # 关闭托管账户
    WITHDRAW = 48  # 提现
    DEPOSIT = 49  # 存款
    TRANSFER = 50  # 转账
    BURN = 51  # 销毁
    BURN_NFT = 52  # 销毁 NFT
    PLATFORM_FEE = 53  # 平台费用
    LOAN = 54  # 贷款
    REPAY_LOAN = 55  # 偿还贷款
    ADD_TO_POOL = 56  # 添加到池
    REMOVE_FROM_POOL = 57  # 从池中移除
    CLOSE_POSITION = 58  # 关闭位置
    UNLABELED = 59  # 未标记
    CLOSE_ACCOUNT = 60  # 关闭账户
    WITHDRAW_GEM = 61  # 提取宝石
    DEPOSIT_GEM = 62  # 存入宝石
    STAKE_TOKEN = 63  # 质押代币
    UNSTAKE_TOKEN = 64  # 解质押代币
    STAKE_SOL = 65  # 质押 SOL
    UNSTAKE_SOL = 66  # 解质押 SOL
    CLAIM_REWARDS = 67  # 领取奖励
    BUY_SUBSCRIPTION = 68  # 购买订阅
    SWAP = 69  # 交换
    INIT_SWAP = 70  # 初始化交换
    CANCEL_SWAP = 71  # 取消交换
    REJECT_SWAP = 72  # 拒绝交换
    INITIALIZE_ACCOUNT = 73  # 初始化账户
    TOKEN_MINT = 74  # 代币铸造
    CREATE_APPARAISAL = 75  # 创建评估
    FUSE = 76  # 融合
    DEPOSIT_FRACTIONAL_POOL = 77  # 存入分数池
    FRACTIONALIZE = 78  # 分数化
    CREATE_RAFFLE = 79  # 创建抽奖
    BUY_TICKETS = 80  # 购买票
    UPDATE_ITEM = 81  # 更新物品
    LIST_ITEM = 82  # 上架物品
    DELIST_ITEM = 83  # 下架物品
    ADD_ITEM = 84  # 添加物品
    CLOSE_ITEM = 85  # 关闭物品
    BUY_ITEM = 86  # 购买物品
    FILL_ORDER = 87  # 完成订单
    UPDATE_ORDER = 88  # 更新订单
    CREATE_ORDER = 89  # 创建订单
    CLOSE_ORDER = 90  # 关闭订单
    CANCEL_ORDER = 91  # 取消订单
    KICK_ITEM = 92  # 踢除物品
    UPGRADE_FOX = 93  # 升级狐狸
    UPGRADE_FOX_REQUEST = 94  # 升级狐狸请求
    LOAN_FOX = 95  # 贷款狐狸
    BORROW_FOX = 96  # 借用狐狸
    SWITCH_FOX_REQUEST = 97  # 切换狐狸请求
    SWITCH_FOX = 98  # 切换狐狸
    CREATE_ESCROW = 99  # 创建托管
    ACCEPT_REQUEST_ARTIST = 100  # 接受艺术家请求
    CANCEL_ESCROW = 101  # 取消托管
    ACCEPT_ESCROW_ARTIST = 102  # 接受艺术家托管
    ACCEPT_ESCROW_USER = 103  # 接受用户托管
    PLACE_BET = 104  # 下赌注
    PLACE_SOL_BET = 105  # 下 SOL 赌注
    CREATE_BET = 106  # 创建赌注
    NFT_RENT_UPDATE_LISTING = 107  # NFT 租赁更新上架
    NFT_RENT_ACTIVATE = 108  # NFT 租赁激活
    NFT_RENT_CANCEL_LISTING = 109  # NFT 租赁取消上架
    NFT_RENT_LISTING = 110  # NFT 租赁上架
    FINALIZE_PROGRAM_INSTRUCTION = 111  # 完成程序指令
    UPGRADE_PROGRAM_INSTRUCTION = 112  # 升级程序指令
    NFT_GLOBAL_BID = 113  # NFT 全球投标
    NFT_GLOBAL_BID_CANCELLED = 114  # NFT 全球投标已取消
    EXECUTE_TRANSACTION = 115  # 执行交易
    APPROVE_TRANSACTION = 116  # 批准交易
    ACTIVATE_TRANSACTION = 117  # 激活交易
    CREATE_TRANSACTION = 118  # 创建交易
    REJECT_TRANSACTION = 119  # 拒绝交易
    CANCEL_TRANSACTION = 120  # 取消交易
    ADD_INSTRUCTION = 121  # 添加指令
    ATTACH_METADATA = 122  # 附加元数据
    REQUEST_PNFT_MIGRATION = 123  # 请求 PNFT 迁移
    START_PNFT_MIGRATION = 124  # 开始 PNFT 迁移
    MIGRATE_TO_PNFT = 125  # 迁移到 PNFT
    UPDATE_RAFFLE = 126  # 更新抽奖
    CREATE_POOL = 127  # 创建池
    ADD_LIQUIDITY = 128  # 添加流动性
    WITHDRAW_LIQUIDITY = 129  # 提取流动性


class Event(ABC):
    type: EventType

    @classmethod
    def is_type(cls, data: Dict) -> bool:
        pass

    @classmethod
    def parse(cls, data: Dict) -> 'Event':
        pass
