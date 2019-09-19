
import psutil
import time

while(1):
    for pid in psutil.pids():
        p = psutil.Process(pid)
        if p.name() == "python.exe":
            print(str(p.cmdline()))
            time.sleep(2)
              

