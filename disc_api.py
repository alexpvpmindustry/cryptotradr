import json
import requests

config = json.load(open("secrets.config","r"))
#channels
STATUS_PING2 = config["status-ping2"]
CRYPTO_SIGNALS2= config["crypto-signals2"]

#roles
SIGNALROLE="<@&1126499478342475807>"
def ping(chnl,strr):
    requests.post(chnl,data={"content":strr})