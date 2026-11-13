python3 csvsum.py < data.csv | md5sum >/dev/null; s=$(date +%s.%N); python3 csvsum.py < data.csv >out.txt; e=$(date +%s.%N)
[ $(wc -l <out.txt) -eq 50 ] && python3 -c "print(1/($e-$s))"
