import winreg
KEY = r"Software\Microsoft\Windows\Windows Error Reporting\LocalDumps\python.exe"
try:
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, KEY)
    print("WER_LOCALDUMP_KEY_REMOVED")
except OSError as e:
    print("WER_CLEANUP:", e.winerror, e)
