screen -ls | grep '(Detached)' | awk '{print }' | xargs -I % -t screen -X -S % quit 
