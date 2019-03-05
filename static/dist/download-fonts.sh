for filename in $(grep -o 'url([^")]*)' font-awesome.css|sed 's/[?#)].*//;s/.*(\.\.\///')
do
	wget https://use.fontawesome.com/releases/v5.7.2/$filename -O $filename
done
