
screen -dmS "run5m" sh -c "/root/miniconda3/condabin/conda activate cryt310_try; echo running5m; python run_trades_ver3.py $1 $2 5m; exec bash;";
screen -dmS "run15m" sh -c "/root/miniconda3/condabin/conda activate cryt310_try; echo running15m; python run_trades_ver3.py $1 $2 15m; exec bash;";
screen -dmS "run30m" sh -c "/root/miniconda3/condabin/conda activate cryt310_try; echo running30m; python run_trades_ver3.py $1 $2 30m; exec bash;";