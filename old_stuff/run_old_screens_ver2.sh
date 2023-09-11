
echo "starting screens from $1 to $2"

val=$1
vae=$2
for i in $(eval echo "{$val..$vae}") 
do 
  echo "starting run$i"
  screen -dmS "run$i" sh -c "/root/miniconda3/condabin/conda activate cryt310; echo running$i; python run_trades_ver2.py $i; exec bash;";
done
echo "done screens$1 to $2"
