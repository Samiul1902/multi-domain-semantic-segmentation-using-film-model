"""Parse a Windows minidump: exception record + module list + faulting module."""
import ctypes
import struct
import sys
from pathlib import Path

dbghelp = ctypes.WinDLL("dbghelp.dll")
dbghelp.MiniDumpReadDumpStream.restype = ctypes.c_int
dbghelp.MiniDumpReadDumpStream.argtypes = [
    ctypes.c_void_p, ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(ctypes.c_ulong),
]

EXCEPTION_STREAM = 6
MODULE_LIST_STREAM = 4


def read_stream(base, number):
    pdir = ctypes.c_void_p()
    pbuf = ctypes.c_void_p()
    size = ctypes.c_ulong()
    ok = dbghelp.MiniDumpReadDumpStream(base, number,
                                        ctypes.byref(pdir), ctypes.byref(pbuf),
                                        ctypes.byref(size))
    if not ok:
        return None, 0
    return pbuf.value, size.value


def u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def u64(data, off):
    return struct.unpack_from("<Q", data, off)[0]


def main(path):
    raw = Path(path).read_bytes()
    buf = ctypes.create_string_buffer(raw, len(raw))
    base = ctypes.cast(buf, ctypes.c_void_p)

    addr, size = read_stream(base, EXCEPTION_STREAM)
    if not addr:
        print("NO_EXCEPTION_STREAM")
        return
    exc = ctypes.string_at(addr, size)
    thread_id = u32(exc, 0)
    code = u32(exc, 8)
    flags = u32(exc, 12)
    rec = u64(exc, 16)
    exaddr = u64(exc, 24)
    nparams = u32(exc, 32)
    info = [u64(exc, 40 + 8 * i) for i in range(min(nparams, 15))]
    print(f"thread_id={thread_id}")
    print(f"exception_code=0x{code:08X}")
    print(f"exception_flags=0x{flags:08X}")
    print(f"exception_record=0x{rec:016X}")
    print(f"exception_address=0x{exaddr:016X}")
    print(f"number_parameters={nparams} info={[hex(i) for i in info]}")
    if code == 0xC0000005 and info:
        print("access_type=", {0: "READ", 1: "WRITE", 8: "EXECUTE"}.get(info[0], info[0]))

    modaddr, modsize = read_stream(base, MODULE_LIST_STREAM)
    if not modaddr:
        print("NO_MODULE_LIST")
        return
    mods = ctypes.string_at(modaddr, modsize)
    n = u32(mods, 0)
    print(f"modules={n}")
    off = 4
    hit = None
    entries = []
    for _ in range(n):
        mod_base = u64(mods, off + 0)
        mod_len = u32(mods, off + 8)
        name_rva = u32(mods, off + 20)
        # MINIDUMP_STRING: ULONG32 Length (bytes) + UTF-16LE; RVA is dump-relative
        slen = u32(raw, name_rva)
        name = raw[name_rva + 4: name_rva + 4 + slen].decode("utf-16-le", "replace")
        entries.append((mod_base, mod_len, name))
        if mod_base <= exaddr < mod_base + mod_len:
            hit = (mod_base, mod_len, name)
        off += 108
    if hit:
        print(f"FAULTING_MODULE={hit[2]}")
        print(f"fault_offset=0x{exaddr - hit[0]:X}")
    else:
        print("FAULTING_MODULE=<none: address not inside any loaded module>")
    # nearest module below the fault address
    below = [e for e in entries if e[0] <= exaddr]
    if below:
        nb = max(below, key=lambda e: e[0])
        print(f"nearest_module_below={nb[2]} base=0x{nb[0]:X} delta=0x{exaddr - nb[0]:X}")
    print("--- last 8 modules loaded (by base) ---")
    for b, l, nm in sorted(entries, key=lambda e: e[0])[-8:]:
        print(f"  0x{b:012X} 0x{l:08X} {nm}")


if __name__ == "__main__":
    main(sys.argv[1])
