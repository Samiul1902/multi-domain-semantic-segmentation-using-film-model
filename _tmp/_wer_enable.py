"""Enable user-scope WER LocalDumps for python.exe (reversible)."""
import winreg

KEY = r"Software\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe"
FOLDER = r"D:\Softfors\jup\_tmp\crashdumps"

with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEY) as k:
    winreg.SetValueEx(k, "DumpFolder", 0, winreg.REG_EXPAND_SZ, FOLDER)
    winreg.SetValueEx(k, "DumpType", 0, winreg.REG_DWORD, 1)   # mini dump
    winreg.SetValueEx(k, "DumpCount", 0, winreg.REG_DWORD, 5)
print("WER_LOCALDUMP_ENABLED", KEY, FOLDER)
