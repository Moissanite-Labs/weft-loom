"""Child process of tests/test_window.py. It starts a run on a fake service, asks a
windowed responder for the first reply, and blocks in the first result() with the
whole window of calls in flight, printing WAITING and the number of calls sent. The
test then kills it. Not a test module."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import codec as C  # noqa: E402
import driver as D  # noqa: E402
import episodes as E  # noqa: E402
import fakes  # noqa: E402
import tinker_backend as T  # noqa: E402


def main(approvals, run_id, window, plan_id):
    sampler = fakes.WindowSampler()

    def hang(self, timeout=None):
        print("WAITING %d" % len(sampler.calls), flush=True)
        time.sleep(300)
    fakes.PendingFuture.result = hang
    svc = fakes.FakeService(base=sampler)
    plan = {"train": 100000, "prefill": 10000, "sample": 10000}
    run = T.TinkerRun(run_id, approvals, plan, "test", plan_id, svc, fakes.FakeTypes)
    codec = C.Codec(fakes.FakeTokenizer())
    views = D.epset_views(E.build_set("train", {"S": 6, "M": 6}), "C")
    resp = T.WindowedResponder(run, run.base_sampler(), codec, 96, views, int(window))
    resp(views[0])
    print(json.dumps("unreachable"))


if __name__ == "__main__":
    main(*sys.argv[1:5])
