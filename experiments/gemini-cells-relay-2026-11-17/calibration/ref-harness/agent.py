"""Reference harness for calibration, written by the lead, not by a cell.

Two changes to the seed: every action in a reply is run, in order, and the first prompt
already shows the folder listing and the instance notes.

Run with the task folder as the working directory. The model is reached through cellapi,
which the referee provides. Everything in this folder may be changed by a builder.
"""
import importlib.util
import os
import sys

import cellapi

HERE = os.path.dirname(os.path.abspath(__file__))
OBS_CAP = 1200       # characters of tool output shown back to the model
MAX_STEPS = 40       # the referee's call cap usually ends the episode first


def load_tools():
    tools = {}
    folder = os.path.join(HERE, "tools")
    for name in sorted(os.listdir(folder)):
        if name.endswith(".py") and not name.startswith("_"):
            spec = importlib.util.spec_from_file_location(name[:-3], os.path.join(folder, name))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            tools[mod.NAME] = mod
    return tools


def parse(reply):
    """Return every (tool, arg, body) action in the reply, in order."""
    lines = reply.splitlines()
    actions, i = [], 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("@") and not line.startswith("@end"):
            head = line[1:].split(None, 1)
            if head and head[0] == "done":
                actions.append(("done", "", ""))
                break
            if head:
                body = []
                i += 1
                while i < len(lines) and lines[i].strip() != "@end":
                    body.append(lines[i])
                    i += 1
                actions.append((head[0], head[1] if len(head) > 1 else "", "\n".join(body)))
        i += 1
    return actions


def survey(cwd):
    """The folder listing and the head of each note file, shown in the first prompt."""
    out = []
    for base, dirs, files in os.walk(cwd):
        for f in sorted(files):
            p = os.path.join(base, f)
            out.append(f"{os.path.relpath(p, cwd)} ({os.path.getsize(p)} bytes)")
    text = "Files:\n" + "\n".join(out[:60])
    for f in sorted(os.listdir(cwd)):
        if f.endswith(".md") and f != "TASK.md":
            with open(os.path.join(cwd, f), errors="replace") as fh:
                text += f"\n\n{f}:\n" + fh.read(4000)
    return text


def main():
    cwd = os.getcwd()
    tools = load_tools()
    with open(os.path.join(HERE, "prompt.md")) as f:
        system = f.read() + "\nTools:\n" + "\n".join(t.HELP for t in tools.values())
    with open(os.path.join(cwd, "TASK.md")) as f:
        task = f.read()
    history = [survey(cwd) + "\n"]
    for step in range(MAX_STEPS):
        left = cellapi.calls_left()
        if left <= 0:
            break
        prompt = "TASK.md:\n" + task + "\n\n" + "".join(history) + f"\nModel calls left: {left}. Your next action:"
        try:
            reply = cellapi.brain(system, prompt)
        except cellapi.BudgetExhausted:
            break
        actions = parse(reply)
        if not actions:
            history.append(f"\n--- step {step + 1} ---\n{reply.strip()[:400]}\n--- result ---\nCould not read an action. Use the @tool ... @end form.\n")
            continue
        results, finished = [], False
        for tool, arg, body in actions:
            if tool == "done":
                finished = True
                break
            if tool not in tools:
                results.append(f"Unknown tool {tool}.")
                continue
            try:
                obs = tools[tool].run(arg, body, {"cwd": cwd})
            except Exception as exc:
                obs = f"Tool error: {type(exc).__name__}: {exc}"
            results.append(obs[:OBS_CAP] + ("\n[output cut]" if len(obs) > OBS_CAP else ""))
        if finished:
            break
        history.append(f"\n--- step {step + 1} ---\n{reply.strip()}\n--- results, one per action ---\n" + "\n---\n".join(results) + "\n")


if __name__ == "__main__":
    sys.exit(main())
