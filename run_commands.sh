
# loop through all runs
for i in {4..5}; do screen -dmS "run$i" sh -c "/root/miniconda3/condabin/conda activate cryt310; echo $i; conda env list; exec bash;"; done

for i in {0..15}; do screen -dmS "run$i" sh -c "/root/miniconda3/condabin/conda activate cryt310; echo running$i; python run_trades0_0_0.py $i; exec bash;"; done

# kill all screens
screen -ls | grep '(Detached)' | awk '{print $1}' | xargs -I % -t screen -X -S % quit
