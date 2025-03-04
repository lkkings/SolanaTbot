# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/3 22:16
@Author     : lkkings
@FileName:  : layouts.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from construct import Struct as CStruct, Int8ul, Int64ul

BORROW_LAYOUT = CStruct('instruction' / Int8ul, 'liquidityAmount' / Int64ul)
REPAY_LAYOUT = CStruct('instruction' / Int8ul, 'liquidityAmount' / Int64ul, 'borrowInstructionIndex' / Int8ul)
