import os, sys
os.execvp('sh', ['sh', '-c', "LC_ALL=C tr -s '[:space:]' '\\n' | LC_ALL=C sort -n"])
