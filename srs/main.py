from tinkoff.invest import Client, InstrumentIdType, Quotation, HistoricCandle
import os
import datetime as dt 
from icecream import ic
import pandas as pd
import numpy as np
from help_tools import *

target_figi_in_groupe = {
    'Акции':['BBG004730N88']
    ,'Облигации':['BBG0024TRF04']
    ,'Металлы':[]
    ,'Финансы':['RUB000UTSTOM']
}

target_rate_on_groupe = {
    'Акции':0.4
    ,'Облигации':0.4
    ,'Металлы':0.2
    ,'Финансы':0
}


class TinkoffStockBalanser:
    def __init__(self, token, account_id):
        self.token = token
        self.account_id = account_id

    def get_rebalance_actions(self):
        current_state = self._get_current_state()
        rebalance_actions = self._get_rebalance_actions_from_curent_state(current_state)
        return rebalance_actions

    def _get_current_state(self):
        token = self.token
        account_id = self.account_id
        with Client(token) as client:
            return self._get_current_state_in_client(client,account_id)

    def _get_current_state_in_client(self,client:Client,account_id):
        # ic(client.users.get_accounts())
        all_positions = []
        for position in client.operations.get_portfolio(account_id=account_id).positions:
            all_positions.append(self._get_position_info(client,position))
        return pd.DataFrame(all_positions)

    def _get_position_info(self,client,position):
        instrument_info = client.instruments.get_instrument_by(id_type=1,id=position.figi).instrument
        anchor_day = dt.datetime.now(dt.timezone.utc) - dt.timedelta(1)
        dates = [day_start(anchor_day),day_end(anchor_day)]
        # ic(anchor_day)
        # ic(dates)
        candles = client.market_data.get_candles(figi=position.figi,from_=dates[0],to=dates[1],interval=5,instrument_id=position.figi).candles
        # ic(candle)
        candle = [candle for candle in candles if candle.time == dates[0]]
        if len(candle) == 0:
            if position.instrument_type == 'currency':
                candle = HistoricCandle(
                    open=Quotation(1,0)
                    ,high=Quotation(1,0)
                    ,low=Quotation(1,0)
                    ,close=Quotation(1,0)
                )
            else:
                raise ValueError(f'Нет обработчика свечей для инструментов этого типа: instrument_type = {position.instrument_type}')
        else:
            candle = candle[0]
        # ic(candle)
        positions_with_info = {
            'figi': position.figi
            ,'ticker':instrument_info.ticker
            ,'instrument_type': position.instrument_type
            ,'quantity': quotation_to_float(position.quantity)
            ,'quantity_lot': quotation_to_float(position.quantity_lots)
            ,'lot': instrument_info.lot
            ,'currency': instrument_info.currency
            ,'name': instrument_info.name
            ,'class_code': instrument_info.class_code
            ,'exchange': instrument_info.exchange
            ,'price': quotation_to_float(candle.close)
        }
        return positions_with_info
    
    def _get_rebalance_actions_from_curent_state(self,current_state):
        current_state = current_state.set_index(current_state['figi'])
        # ic(ap)
        # ic(ap[['quantity_lot','lot','price','quantity']])
        full_price = current_state['quantity'] * current_state['price']
        # ic(full_price)
        total = full_price.sum() 
        # ic(total)
        rate = full_price/total
        # ic(rate)
        target_rate = self._get_target_rate()

        delta_rate = target_rate - rate
        # ic(delta_rate)
        delta_price = delta_rate * full_price
        # ic(delta_price) 
        delta_quantity = delta_price / current_state['price']
        # ic(delta_quantity) 
        delta_lot = (delta_quantity / current_state['lot']).round()
        delta_lot.name = 'lot_changes'
        # ic(delta_lot)
        result = current_state.merge(delta_lot,left_index=True,right_index=True)[['figi','ticker','name','lot_changes']]
        return result
    
    def _get_target_rate(self):
        figis = pd.Series(target_figi_in_groupe)
        rate = pd.Series(target_rate_on_groupe)
        df = pd.DataFrame({'figis':figis,'groupe_rate':rate})
        df['len'] = df['figis'].apply(len)
        df['element_rate'] = (df['groupe_rate']/df['len']).replace(np.inf,0)
        df['element_rate'] = df['element_rate'] / df['element_rate'].sum()

        target_rate = df[['figis','element_rate']].explode('figis').dropna()
        target_rate = target_rate.set_index(target_rate['figis'])
        # ic(target_rate)
        
        return target_rate['element_rate']

if __name__ == '__main__':
    token = os.getenv('TINKOFF_API_TOKEN')
    account_id = '2224375246'
    ra = TinkoffStockBalanser(token,account_id).get_rebalance_actions()
    ic(ra)