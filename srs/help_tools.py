from tinkoff.invest import Client, InstrumentIdType, Quotation, HistoricCandle
import os
import datetime as dt 
from icecream import ic
import pandas as pd
import numpy as np

def day_start(day: dt.datetime):
    return dt.datetime(day.year, day.month, day.day, tzinfo=day.tzinfo)

def day_end(day: dt.datetime):
    return dt.datetime(day.year, day.month, day.day, tzinfo=day.tzinfo) + dt.timedelta(days=1)# - dt.timedelta(seconds=1)

def quotation_to_float(q: Quotation):
    return float(q.units) + float(q.nano/10**9)