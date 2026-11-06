import ctypes, struct, sys
from pathlib import Path
dbghelp = ctypes.WinDLL("dbghelp.dll")
dbghelp.MiniDumpReadDumpStream.restype = ctypes.c_int
dbghelp.MiniDumpReadDumpStream.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
    ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_ulong)]
raw = Path(sys.argv[1]).read_bytes()
buf = ctypes.create_string_buffer(raw, len(raw)); base = ctypes.cast(buf, ctypes.c_void_p)
def stream(n):
    d=ctypes.c_void_p(); b=ctypes.c_void_p(); s=ctypes.c_ulong()
    if not dbghelp.MiniDumpReadDumpStream(base,n,ctypes.byref(d),ctypes.byref(b),ctypes.byref(s)): return None,0
    return b.value, s.value
u32=lambda d,o: struct.unpack_from("<I",d,o)[0]
u64=lambda d,o: struct.unpack_from("<Q",d,o)[0]
a,s=stream(4); mods=ctypes.string_at(a,s); n=u32(mods,0)
exaddr=0xE87F931B
print("n=",n)
print("reconstructed 0x7FFCE87F931B:")
recon=0x7FFC00000000|exaddr
for i in range(n):
    o=4+i*108; mb=u64(mods,o); ml=u32(mods,o+8); rva=u32(mods,o+20)
    sl=u32(raw,rva); nm=raw[rva+4:rva+4+sl].decode('utf-16-le','replace')
    tag=""
    if mb<=recon<mb+ml: tag=" <== RECONSTRUCTED MATCH"
    if mb<=exaddr<mb+ml: tag+=" <== DIRECT MATCH"
    print(f"0x{mb:012X} 0x{ml:08X} {nm}{tag}")
