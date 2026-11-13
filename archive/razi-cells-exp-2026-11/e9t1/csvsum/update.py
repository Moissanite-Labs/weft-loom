with open("_csvsum.c") as f:
    code = f.read()
import re
print("Functions:", re.findall(r'void\s+(\w+)\s*\(', code))
