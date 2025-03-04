# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/8 16:25
@Author     : lkkings
@FileName:  : base_layout.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from abc import ABC, abstractmethod
from construct import Struct as CStruct
from solders.pubkey import Pubkey


class Layout(ABC):

    @classmethod
    def get_layout(cls, program_id: Pubkey) -> CStruct:
        raise NotImplementedError
