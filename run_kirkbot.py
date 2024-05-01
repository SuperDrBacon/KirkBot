import subprocess
import threading

def run_admin_portal() -> None:
    subprocess.run(["python.exe", "admin_portal.py"])

def run_kirkbot() -> None:
    subprocess.run(["python.exe", "KirkBot.py"])

if __name__ == "__main__":
    thread1 = threading.Thread(target=run_admin_portal)
    thread2 = threading.Thread(target=run_kirkbot)
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()