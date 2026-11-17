"""Run shell commands in the working folder."""
import subprocess

NAME = "sh"
HELP = "@sh ... @end : run shell commands in your folder (python3 is available, 20 s limit)"


def run(arg, body, ctx):
    try:
        p = subprocess.run(body, shell=True, capture_output=True, text=True, timeout=20, cwd=ctx["cwd"])
        return (p.stdout + p.stderr) or "(no output)"
    except subprocess.TimeoutExpired:
        return "(timed out after 20 s)"
