import ctypes, ctypes.wintypes as wt, sys
psapi = ctypes.WinDLL('psapi'); k32 = ctypes.WinDLL('kernel32')
psapi.EnumProcessModules.argtypes=[wt.HANDLE, ctypes.POINTER(wt.HMODULE), wt.DWORD, ctypes.POINTER(wt.DWORD)]
psapi.EnumProcessModules.restype=wt.BOOL
psapi.GetModuleFileNameExW.argtypes=[wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]
psapi.GetModuleFileNameExW.restype=wt.DWORD
k32.GetCurrentProcess.restype=wt.HANDLE
k32.OpenProcess.argtypes=[wt.DWORD, wt.BOOL, wt.DWORD]; k32.OpenProcess.restype=wt.HANDLE
h = k32.GetCurrentProcess() if sys.argv[1]=='self' else k32.OpenProcess(0x0410, False, int(sys.argv[1]))
label = 'self(py.exe child)' if sys.argv[1]=='self' else f'pid {sys.argv[1]}'
arr=(wt.HMODULE*4096)(); need=wt.DWORD()
ok=psapi.EnumProcessModules(h, arr, ctypes.sizeof(arr), ctypes.byref(need))
print(label,'ok=',bool(ok),'modules=',need.value//ctypes.sizeof(wt.HMODULE))
hit=[]
for i in range(need.value//ctypes.sizeof(wt.HMODULE)):
    buf=ctypes.create_unicode_buffer(1024)
    psapi.GetModuleFileNameExW(h, arr[i], buf, 1024)
    if 'tsbx' in buf.value.lower(): hit.append(buf.value)
print('  tsbx:',hit if hit else 'ABSENT')
