"""Seed harness. The loop, the prompt and the tools a cell starts with.

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
    """Return (tool, arg, body) for the first action in the reply, or None."""
    lines = reply.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("@") and not line.startswith("@end"):
            head = line[1:].split(None, 1)
            if not head:
                continue
            body = []
            for nxt in lines[i + 1:]:
                if nxt.strip() == "@end":
                    break
                body.append(nxt)
            return head[0], (head[1] if len(head) > 1 else ""), "\n".join(body)
    return None


def main():
    cwd = os.getcwd()
    tools = load_tools()
    with open(os.path.join(HERE, "prompt.md")) as f:
        system = f.read() + "\nTools:\n" + "\n".join(t.HELP for t in tools.values())
    with open(os.path.join(cwd, "TASK.md")) as f:
        task = f.read()
    history = []
    for step in range(MAX_STEPS):
        left = cellapi.calls_left()
        if left <= 0:
            break
        prompt = "TASK.md:\n" + task + "\n\n" + "".join(history) + f"\nModel calls left: {left}. Your next action:"
        try:
            reply = cellapi.brain(system, prompt)
        except cellapi.BudgetExhausted:
            break
        action = parse(reply)
        if action is None:
            obs = "Could not read an action. Use the @tool ... @end form."
        elif action[0] == "done":
            break
        elif action[0] not in tools:
            obs = f"Unknown tool {action[0]}."
        else:
            try:
                obs = tools[action[0]].run(action[1], action[2], {"cwd": cwd})
            except Exception as exc:
                obs = f"Tool error: {type(exc).__name__}: {exc}"
        if len(obs) > OBS_CAP:
            obs = obs[:OBS_CAP] + "\n[output cut]"
        history.append(f"\n--- step {step + 1} ---\n{reply.strip()}\n--- result ---\n{obs}\n")


if __name__ == "__main__":
    sys.exit(main())
