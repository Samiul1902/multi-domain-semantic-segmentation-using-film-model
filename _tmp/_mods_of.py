import ctypes, ctypes.wintypes as wt, sys
psapi = ctypes.WinDLL('psapi'); k32 = ctypes.WinDLL('kernel32')
def mods(h):
    arr=(ctypes.c_void_p*2048)(); need=wt.DWORD()
    if not psapi.EnumProcessModules(h, ctypes.byref(arr), ctypes.sizeof(arr), ctypes.byref(need)): return []
    out=[]
    for i in range(need.value//ctypes.sizeof(ctypes.c_void_p)):
        buf=ctypes.create_unicode_buffer(1024)
        psapi.GetModuleFileNameExW(h, arr[i], buf, 1024)
        out.append((arr[i], buf.value))
    return out
if sys.argv[1]=='self':
    h=k32.GetCurrentProcess(); label='py.exe-launched python'
else:
    h=k32.OpenProcess(0x1000|0x0010, False, int(sys.argv[1])); label=f'pid {sys.argv[1]}'
ms=mods(h)
print(label,'modules=',len(ms))
for b,n in ms:
    if 'tsbx' in n.lower() or 'sandbox' in n.lower(): print('  TS_BX:',hex(b),n)
print('  has_tsbx=',any('tsbx' in n.lower() for _,n in ms))
