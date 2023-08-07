
screen -dmS "run5m" sh  -c "/root/miniconda3/condabin/conda activate cryt310; echo running5m; python aver5_run_trades.py 0 40 5m; exec bash;";
screen -dmS "run15m" sh -c "/root/miniconda3/condabin/conda activate cryt310; echo running15m; python aver5_run_trades.py 40 80 15m; exec bash;";
screen -dmS "run30m" sh -c "/root/miniconda3/condabin/conda activate cryt310; echo running30m; python aver5_run_trades.py 80 120 30m; exec bash;";
