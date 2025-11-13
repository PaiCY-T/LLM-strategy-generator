from finlab.backtest import sim

close = data.get('price:收盤價')
pct_change = (close / close.shift() - 1).rolling(5).mean()
當月營收 = data.get('monthly_revenue:當月營收')

pos = pct_change[(close > close.average(60)) & (close > close.average(20)) & (close > close.average(120)) & (當月營收.average(3) > 當月營收.average(12))].is_largest(10)

r = sim(pos, resample='M', resample_offset='11D', upload=False, stop_loss=0.1)
r.display()