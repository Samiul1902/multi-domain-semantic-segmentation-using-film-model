import ctypes, ctypes.wintypes as wt, sys
psapi=ctypes.WinDLL('psapi'); k32=ctypes.WinDLL('kernel32')
psapi.EnumProcessModules.argtypes=[wt.HANDLE, ctypes.POINTER(wt.HMODULE), wt.DWORD, ctypes.POINTER(wt.DWORD)]; psapi.EnumProcessModules.restype=wt.BOOL
psapi.GetModuleFileNameExW.argtypes=[wt.HANDLE, wt.HMODULE, wt.LPWSTR, wt.DWORD]; psapi.GetModuleFileNameExW.restype=wt.DWORD
k32.GetCurrentProcess.restype=wt.HANDLE
h=k32.GetCurrentProcess()
arr=(wt.HMODULE*4096)(); need=wt.DWORD()
psapi.EnumProcessModules(h, arr, ctypes.sizeof(arr), ctypes.byref(need))
print('modules=', need.value//ctypes.sizeof(wt.HMODULE))
for i in range(need.value//ctypes.sizeof(wt.HMODULE)):
    b=ctypes.create_unicode_buffer(1024); psapi.GetModuleFileNameExW(h, arr[i], b, 1024)
    low=b.value.lower()
    if any(k in low for k in ('eset','ebeh','tsbx','sandbox','ekrn')):
        print('  INJECT:', b.value)
