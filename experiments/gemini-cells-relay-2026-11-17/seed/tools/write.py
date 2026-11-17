"""Create or overwrite a file."""
import os

NAME = "write"
HELP = "@write <path> ... @end : create or overwrite a file with the given content"


def run(arg, body, ctx):
    path = os.path.join(ctx["cwd"], arg.strip())
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(body if body.endswith("\n") else body + "\n")
    return f"wrote {arg.strip()} ({len(body)} chars)"
