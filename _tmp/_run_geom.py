import subprocess
p=subprocess.run([r"D:/Softfors/jup/.venv/Scripts/python.exe", r"D:/Softfors/jup/_tmp/_geom.py"], cwd=r"D:/Softfors/jup", capture_output=True, text=True)
print(p.stdout); print("ERR", p.stderr[-600:])
