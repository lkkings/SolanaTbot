import requests

from solders.keypair import Keypair

# # 创建webhook
# response = requests.post(
#     "https://api.helius.xyz/v0/webhooks?api-key=4aa1fdf0-7659-416a-b072-be1a626f9a1d",
#     headers={"Content-Type":"application/json"},
#     json={
#          "webhookURL": "https://TestServer.test.repl.co/webhooks",
#          "transactionTypes": ["Any"],
#          "accountAddresses": [str(Keypair().pubkey()) for i in range(90000)],
#          "webhookType": "raw",
#          "authHeader": None
#     }
# )
#
# data = response.json()
# print(data)
# print(len(data['accountAddresses']))
# print(data['webhookID'])

# 获取所有的webhook
import requests

response = requests.get(
    "https://api.helius.xyz/v0/webhooks?api-key=4aa1fdf0-7659-416a-b072-be1a626f9a1d",
    headers={"Content-Type":"application/json"},
)
data = response.json()
print(data)
print(len(data[0]['accountAddresses']))
print(data[0]['webhookID'])
"""
[
{'webhookID': 'c73e75c2-a669-4bd0-b3f8-9cf0b7d86ad8',
 'project': 'b732dfd7-4134-49b3-9c98-f2ebd6318db7',
  'wallet': 'lkkings888@gmail.com', 
  'webhookURL': 'https://TestServer.test.repl.co/webhooks', 
  'accountAddresses': ['675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'],
   'transactionTypes': ['Any'], 'webhookType': 'raw', 'txnStatus': 'all'}
   ]
"""

# 获取指定webhook
# import requests
#
# response = requests.get(
#     "https://api.helius.xyz/v0/webhooks/6a83ac30-e4e1-4f7b-a9d4-b74e03fd9e12?api-key=4aa1fdf0-7659-416a-b072-be1a626f9a1d",
#     headers={"Content-Type":"application/json"},
#     json=None
# )
# data = response.json()
# print(data)
"""
{'webhookID': 'c73e75c2-a669-4bd0-b3f8-9cf0b7d86ad8',
 'project': 'b732dfd7-4134-49b3-9c98-f2ebd6318db7', 
 'wallet': 'lkkings888@gmail.com',
  'webhookURL': 'https://TestServer.test.repl.co/webhooks',
   'accountAddresses': ['675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8'],
    'transactionTypes': ['Any'], 
    'webhookType': 'raw', 
    'txnStatus': 'all'}
"""
#
# 删除指定webhook
import requests

response = requests.delete(
    f"https://api.helius.xyz/v0/webhooks/{data[0]['webhookID']}?api-key=4aa1fdf0-7659-416a-b072-be1a626f9a1d",
    headers={},
)
print(response.text)
