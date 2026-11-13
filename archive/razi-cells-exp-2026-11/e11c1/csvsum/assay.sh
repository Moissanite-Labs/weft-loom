s=$(date +%s.%N)
python3 csvsum.py < big.csv > out.txt
e=$(date +%s.%N)
cmp -s out.txt exp.txt && python3 -c "print(round(1/($e-$s),3))" || echo 0
