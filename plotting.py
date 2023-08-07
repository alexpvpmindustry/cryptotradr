import matplotlib.pyplot as plt 
import numpy as np

def plot_profits(profits,title="",fee=-0.002,axx=None,savefig=""):
    """profits are the profits from each trade, in fractions: [0.01,-0.02,0.05] """
    if axx is None:
        fig,axx=plt.subplots(3,1) 
    winpercent=len(np.where((np.asarray(profits)+fee)>0)[0])/len(profits)
    ax=axx[0]
    ax.set_ylabel("equity")
    equity = [1]
    equity_fee = [1]
    for p in profits:
        equity.append(equity[-1]*(1+p))
        equity_fee.append(equity_fee[-1]*(1+p-0.002))
    ax.plot(equity,"-x")
    ax.plot(equity_fee,"-x",label="with fee")
    ax.legend()
    strr=f"{title}\nequity={equity_fee[-1]-1:+.2%}, win%={winpercent:.1%}, Ntrds={len(profits)}\n"
    ax.set_title(strr)

    ax=axx[1]
    ax.hist(profits,bins=100);
    ax.axvline(0.002,c="r",ls="--")
    ax.axvline(0.0,c="r")
    ax.axvline(np.mean(profits),c="g",label=f"mean {np.mean(profits):+.2%}")
    ax.axvline(np.mean(profits)+np.std(profits),c="g",ls="--",label=f"std  $\pm${np.std(profits):.2%}")
    ax.axvline(np.mean(profits)-np.std(profits),c="g",ls="--")
    ax.set_ylabel("mean gains")
    ax.legend()
    ax=axx[2]
    ax.plot(np.asarray(profits)+1,"-x")
    ax.set_ylabel("change per trade")
    if savefig:
        plt.savefig(savefig)
    else:
        plt.show()
    return axx