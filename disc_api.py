import json
import requests
import random

config = json.load(open("secrets.config","r"))
#channels
STATUS_PING2 = config["status-ping2"]
CRYPTO_SIGNALS2= config["crypto-signals2"]
ERROR_PING2= config["error-ping2"]
CRYPTO_LOGS2=config["crypto-logs2"]
#roles
SIGNALROLE="<@&1126499478342475807>"
ALEXPING="<@612861256189083669>"

def ping(chnl,strr):
    requests.post(chnl,data={"content":strr})

def pingfile(chnl,strr,filename,file=""):
    """file=open('fig_temp3.png', 'rb')
    example usage: 
    pingfile(ERROR_PING2,strr,"hehe.txt","open('fig_temp3.png', 'rb')\nwfgwefwef")
    pingfile(ERROR_PING2,strr,"hehe.png",open('fig_temp3.png', 'rb'))
    """
    requests.post(chnl,data={"content":strr},
                  files = {'files': (filename,file )})

emojis='🍏🍎🍐🍊🍋🍌🍉🍇🍓🫐🍈🍒🍑🥭🍍🥥🥝🍅🍆'\
'🥑🥦🥬🥒🌶🫑🌽🥕🫒🧄🧅🥔🍠🥐🥯🍞🥖🥨🧀🥚'\
'🍳🧈🥞🧇🥓🥩🍗🍖🦴🌭🍔🍟🍕🫓🥪🥙🧆🌮🌯🫔'\
'🥗🥘🫕🥫🍝🍜🍲🍛🍣🍱🥟🦪🍤🍙🍚🍘🍥🥠🥮🍢'\
'🍡🍧🍨🍦🥧🧁🍰🎂🍮🍭🍬🍫🍿🍩🍪🌰🥜🍯🥛🍼'\
'🫖☕️🍵🧃🥤🧋🍶🍺🍻🥂🍷🥃🍸🍹🧉🍾🧊🥄🍴🍽🥣🥡'

def get_random_emoji():
    return random.choice(emojis)