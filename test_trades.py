from trader import market_trade

print("buy")
a1,a2,a3 = market_trade("LTCUSDT",0.15,True,False)

print(a1)
print(a2)
print(a3)

print("selling")
a1,a2,a3 = market_trade("LTCUSDT",0.15,False,False)

print(a1)
print(a2)
print(a3)