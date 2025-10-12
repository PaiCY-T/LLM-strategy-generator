from finlab import backtest
from finlab import data

cap = data.get('etl:market_value')
vol = data.get('price:成交股數')
close = data.get('price:收盤價')

std = close.pct_change().rolling(60).std().rank(axis=1, pct=True)

position = cap[
    (vol.average(20) > 200_000)
    & (close > close.average(60)) 
    & (close > close.average(120))
    & (close > close.average(250))
    & (std < 0.7)
].is_smallest(15)

r = backtest.sim(position, resample='Q')