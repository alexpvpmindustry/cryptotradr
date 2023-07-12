import json
import requests
import random

config = json.load(open("secrets.config","r"))
#channels
STATUS_PING2 = config["status-ping2"]
CRYPTO_SIGNALS2= config["crypto-signals2"]
ERROR_PING2= config["error-ping2"]

#roles
SIGNALROLE="<@&1126499478342475807>"
ALEXPING="<@612861256189083669>"

def ping(chnl,strr):
    requests.post(chnl,data={"content":strr})

emojis='🍏🍎🍐🍊🍋🍌🍉🍇🍓🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆'\
'🥑🥦🥬🥒🌶🫑🌽🥕🫒🧄🧅🥔🍠🥐🥯🍞🥖🥨🧀🥚'\
'🍳🧈🥞🧇🥓🥩🍗🍖🦴🌭🍔🍟🍕🫓🥪🥙🧆🌮🌯🫔'\
'🥗🥘🫕🥫🍝🍜🍲🍛🍣🍱🥟🦪🍤🍙🍚🍘🍥🥠🥮🍢'\
'🍡🍧🍨🍦🥧🧁🍰🎂🍮🍭🍬🍫🍿🍩🍪🌰🥜🍯🥛🍼'\
'🫖☕️🍵🧃🥤🧋🍶🍺🍻🥂🍷🥃🍸🍹🧉🍾🧊🥄🍴🍽🥣🥡'

def get_random_emoji():
    return random.choice(emojis)