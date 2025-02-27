from tinkoff.invest import Client
import os
from icecream import ic

token = os.getenv('TINKOFF_API_TOKEN')


with Client(token) as client:
    ic(client.users.get_accounts())
    ic(client.operations.get_portfolio(account_id='2224375246').positions)