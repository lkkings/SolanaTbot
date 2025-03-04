# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/24 22:37
@Author     : lkkings
@FileName:  : types.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
from typing import NamedTuple


class ApiPoolInfoItem(NamedTuple):
    id: str
    mintA: str
    mintB: str
    vaultA: str
    vaultB: str