screen -ls | grep '*trader*(Detached)' | awk '{print $1}' | xargs -I % -t screen -X -S % quit 
