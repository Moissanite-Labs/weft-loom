python3 csvsum.py < d.csv | md5sum >/dev/null
s=$(date +%s.%N); python3 csvsum.py < d.csv >o.txt; e=$(date +%s.%N)
[ $(wc -l <o.txt) -eq 100 ] && echo "1/($e-$s)" | bc -l || echo 0
