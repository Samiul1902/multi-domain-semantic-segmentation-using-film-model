"""Walk the crashing thread stack: caller return address + module-resident frames."""
import ctypes
import struct
import sys
from pathlib import Path

dbghelp = ctypes.WinDLL("dbghelp.dll")
dbghelp.MiniDumpReadDumpStream.restype = ctypes.c_int
dbghelp.MiniDumpReadDumpStream.argtypes = [
    ctypes.c_void_p, ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p),
    ctypes.POINTER(ctypes.c_ulong)]

raw = Path(sys.argv[1]).read_bytes()
buf = ctypes.create_string_buffer(raw, len(raw))
base = ctypes.cast(buf, ctypes.c_void_p)


def stream(n):
    d = ctypes.c_void_p(); b = ctypes.c_void_p(); s = ctypes.c_ulong()
    if not dbghelp.MiniDumpReadDumpStream(base, n, ctypes.byref(d),
                                          ctypes.byref(b), ctypes.byref(s)):
        return None, 0
    return b.value, s.value


def u32(d, o): return struct.unpack_from("<I", d, o)[0]
def u64(d, o): return struct.unpack_from("<Q", d, o)[0]


# modules
a, s = stream(4)
mods = ctypes.string_at(a, s)
n = u32(mods, 0)
ranges = []
for i in range(n):
    o = 4 + i * 108
    mb = u64(mods, o); ml = u32(mods, o + 8); rva = u32(mods, o + 20)
    sl = u32(raw, rva)
    nm = raw[rva + 4:rva + 4 + sl].decode("utf-16-le", "replace")
    ranges.append((mb, ml, nm))


def name_of(addr):
    for mb, ml, nm in ranges:
        if mb <= addr < mb + ml:
            return f"{Path(nm).name}+0x{addr - mb:X}"
    return None


# exception stream -> thread context
a, s = stream(6)
exc = ctypes.string_at(a, s)
exaddr = u64(exc, 24)
ctx_size = u32(exc, 160)
ctx_rva = u32(exc, 164)
ctx = raw[ctx_rva:ctx_rva + ctx_size]
rsp = u64(ctx, 0x98)
rip = u64(ctx, 0xF8)
print(f"exception_address=0x{exaddr:X} ({name_of(exaddr) or 'NO_MODULE'})")
print(f"truncated_reconstruction=0x7FFB{exaddr:08X} -> {name_of(0x7FFB00000000 | exaddr) or 'NO_MODULE'}")
print(f"rip=0x{rip:X} ({name_of(rip) or 'NO_MODULE'})")
print(f"rsp=0x{rsp:X}")

# memory list (stream 5)
a, s = stream(5)
frames = []
if a:
    mem = ctypes.string_at(a, s)
    nr = u32(mem, 0)
    print(f"memory_ranges={nr}")
    stack = None
    for i in range(nr):
        o = 4 + i * 16
        start = u64(mem, o)
        dsize = u32(mem, o + 8)
        drva = u32(mem, o + 12)
        if start <= rsp < start + dsize:
            stack = (start, dsize, drva)
            break
    if stack:
        start, dsize, drva = stack
        blob = raw[drva:drva + dsize]
        off = rsp - start
        print(f"stack_range=0x{start:X}+0x{dsize:X} rsp_offset=0x{off:X}")
        words = []
        for j in range(0, min(dsize - off, 0x800), 8):
            w = struct.unpack_from("<Q", blob, off + j)[0]
            nm = name_of(w)
            if nm:
                words.append((rsp + j, w, nm))
        print("--- module-resident words on stack (first 18) ---")
        for addr, w, nm in words[:18]:
            print(f"  [0x{addr:012X}] 0x{w:012X}  {nm}")
        print(f"first_word_at_rsp=0x{struct.unpack_from('<Q', blob, off)[0]:X} -> {name_of(struct.unpack_from('<Q', blob, off)[0])}")
    else:
        print("stack range for rsp not present in dump")
else:
    print("no MemoryListStream")
