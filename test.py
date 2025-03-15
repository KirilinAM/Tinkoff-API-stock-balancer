from tinkoff.invest import Client, InstrumentIdType, Quotation, HistoricCandle
import os
import datetime as dt 
from icecream import ic
import pandas as pd

def get_target_rate() -> pd.Series:
    return pd.Series([
        0.5
        ,0.5
    ])

def day_start(day: dt.datetime):
    return dt.datetime(day.year, day.month, day.day, tzinfo=day.tzinfo)

def day_end(day: dt.datetime):
    return dt.datetime(day.year, day.month, day.day, tzinfo=day.tzinfo) + dt.timedelta(days=1)# - dt.timedelta(seconds=1)

def quotation_to_float(q: Quotation):
    return float(q.units) + float(q.nano/10**9)

token = os.getenv('TINKOFF_API_TOKEN')
account_id = '2224375246'
with Client(token) as client:
    # ic(client.users.get_accounts())
    all_positions = []
    for position in client.operations.get_portfolio(account_id=account_id).positions:
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
        all_positions.append(positions_with_info)

ap = pd.DataFrame(all_positions)
# ic(ap)
# ic(ap[['quantity_lot','lot','price','quantity']])
full_price = ap['quantity'] * ap['price']
# ic(full_price)
total = full_price.sum() 
# ic(total)
rate = full_price/total
# ic(rate)
target_rate = get_target_rate()
delta_rate = target_rate - rate
# ic(delta_rate)
delta_price = delta_rate * full_price
# ic(delta_price) 
delta_quantity = delta_price / ap['price']
# ic(delta_quantity) 
delta_lot = (delta_quantity / ap['lot']).round()
delta_lot.name = 'lot_changes'
# ic(delta_lot)
result = ap.merge(delta_lot,left_index=True,right_index=True)[['figi','ticker','name','lot_changes']]
ic(result)