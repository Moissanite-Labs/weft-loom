import ctypes
import os
import shlex
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "sortints_helper.c")
_SO = os.path.join(_HERE, "sortints_helper.so")


def _compile(native):
    tmp = "%s.%d.%s.tmp" % (_SO, os.getpid(), "native" if native else "generic")
    cc = shlex.split(os.environ.get("CC") or "cc")
    cmd = cc + ["-std=c11", "-O3", "-fPIC", "-shared"]
    if native:
        cmd.append("-march=native")
    cmd += [_SRC, "-o", tmp]
    try:
        ok = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL).returncode == 0
        if ok:
            os.replace(tmp, _SO)
            return True
    except (OSError, ValueError):
        pass
    try:
        os.unlink(tmp)
    except OSError:
        pass
    return False


def _load_helper():
    if not os.path.exists(_SRC):
        return None
    try:
        stale = (not os.path.exists(_SO) or
                 os.path.getmtime(_SRC) > os.path.getmtime(_SO))
    except OSError:
        stale = True
    if stale and not _compile(True) and not _compile(False):
        return None
    try:
        return ctypes.CDLL(_SO)
    except OSError:
        # Existing binary may be for a different architecture; rebuild generically.
        if _compile(False):
            try:
                return ctypes.CDLL(_SO)
            except OSError:
                pass
        return None


def _python_sort(data):
    nums = list(map(int, data.split()))
    nums.sort()
    if nums:
        out = ("\n".join(map(str, nums)) + "\n").encode("ascii")
        try:
            sys.stdout.buffer.write(out)
        except AttributeError:
            sys.stdout.write(out.decode("ascii"))


def main():
    data = sys.stdin.buffer.read()
    lib = _load_helper()
    if lib is not None:
        outfd = None
        try:
            out = sys.stdout.buffer
            out.flush()
            outfd = out.fileno()
        except (AttributeError, OSError, ValueError):
            outfd = None
        if outfd is not None:
            try:
                fn = lib.sortints_process
                fn.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int)
                fn.restype = ctypes.c_int
                ptr = ctypes.cast(ctypes.c_char_p(data), ctypes.c_void_p)
                rc = fn(ptr, len(data), outfd)
            except (AttributeError, OSError):
                rc = 2
            if rc == 0:
                return
            if rc == -1:
                raise OSError("failed to write sorted integers")
    _python_sort(data)


if __name__ == "__main__":
    main()
