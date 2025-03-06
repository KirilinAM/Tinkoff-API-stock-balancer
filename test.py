from tinkoff.invest import Client, InstrumentIdType, Quotation, HistoricCandle
import os
import datetime as dt 
from icecream import ic

def day_start(day: dt.datetime):
    return dt.datetime(day.year, day.month, day.day, tzinfo=day.tzinfo)

def day_end(day: dt.datetime):
    return dt.datetime(day.year, day.month, day.day, tzinfo=day.tzinfo) + dt.timedelta(days=1)# - dt.timedelta(seconds=1)

token = os.getenv('TINKOFF_API_TOKEN')
account_id = '2224375246'
with Client(token) as client:
    # ic(client.users.get_accounts())
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
        deep_position = {
            'figi': position.figi
            ,'instrument_type': position.instrument_type
            ,'quantity': position.quantity
            ,'quantity_lot': position.quantity_lots
            ,'lot': instrument_info.lot
            ,'currency': instrument_info.currency
            ,'name': instrument_info.name
            ,'class_code': instrument_info.class_code
            ,'exchange': instrument_info.exchange
            ,'price': candle.close
        }
        ic(deep_position)