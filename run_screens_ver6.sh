
#screen -dmS "run_ver6" sh  -c "/root/miniconda3/condabin/conda activate cryt310; echo running_ver_6; python aver6_run_trades.py ; exec bash;";
#screen -dmS "run_ver6_real" sh  -c "/root/miniconda3/condabin/conda activate cryt310; echo running_ver_6; python aver6_run_trades3.py ; exec bash;";
screen -dmS "run_ver6_test" sh  -c "/root/miniconda3/condabin/conda activate cryt310; echo running_ver_6; python aver6_run_trades4.py ; exec bash;";


