s=$(date +%s.%N)
python3 csvsum.py<data.csv>out.txt
e=$(date +%s.%N)
cmp -s out.txt exp.txt && python3 -c "print(1/($e-$s))" || echo 0
