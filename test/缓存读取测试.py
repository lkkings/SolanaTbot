# -*- coding: utf-8 -*-
"""
@Description: 
@Date       : 2024/9/15 23:19
@Author     : lkkings
@FileName:  : 缓存读取测试.py
@Github     : https://github.com/lkkings
@Mail       : lkkings888@gmail.com
-------------------------------------------------
Change Log  :

"""
import pickle

with open(f'./raydium_update_accounts.obj', 'rb') as file:
    data = pickle.load(file)
print()