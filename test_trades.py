from aver6_trader import market_trade

print("buy")
a1,a2,a3 = market_trade("LTCUSDT",0.25,buy=True,test=False)

print(a1)
print(a2)
print(a3)

print("selling")
a1,a2,a3 = market_trade("LTCUSDT",0.25,buy=False,test=False)

print(a1)
print(a2)
print(a3)
