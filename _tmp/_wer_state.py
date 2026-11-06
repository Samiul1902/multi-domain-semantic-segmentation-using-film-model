import winreg, os, pathlib
def rd(root, path, name):
    try:
        with winreg.OpenKey(root, path) as k:
            return winreg.QueryValueEx(k, name)[0]
    except OSError as e:
        return f"<{e.winerror}>"
base = r"Software\Microsoft\Windows\Windows Error Reporting"
print("HKCU Disabled:", rd(winreg.HKEY_CURRENT_USER, base, "Disabled"))
print("HKLM Disabled:", rd(winreg.HKEY_LOCAL_MACHINE, base, "Disabled"))
print("HKLM LocalDumps:", rd(winreg.HKEY_LOCAL_MACHINE, base+r"\LocalDumps", "DumpFolder"))
print("LOCALAPPDATA:", os.environ.get("LOCALAPPDATA"))
p = pathlib.Path(os.environ.get("LOCALAPPDATA",""))/"CrashDumps"
print("CrashDumps exists:", p.exists(), "files:", list(p.glob("*.dmp"))[:5] if p.exists() else None)
