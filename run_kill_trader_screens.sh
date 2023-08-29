screen -ls | grep 'trader' | awk '{print $1}' | xargs -I % -t screen -X -S % quit 
