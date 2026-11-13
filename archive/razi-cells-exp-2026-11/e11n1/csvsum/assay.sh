s=$(date +%s.%N)
python3 csvsum.py <data.csv >/tmp/o
e=$(date +%s.%N)
if [ "$(wc -l </tmp/o)" = 50 ] && [ "$(head -1 /tmp/o)" = "c0,2004069.21" ]; then
python3 -c "print(1/($e-$s))"
else echo 0; fi
