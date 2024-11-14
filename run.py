import subprocess
import schedule
import time

# 定时任务程序
# linux后台运行命令 ：nohup python3 run.py > output.log 2>&1 &
def run_other_script():
    script_path = "./main.py"  
    subprocess.run(["python3", script_path])

# 每天8:30执行任务
schedule.every().day.at("08:30").do(run_other_script)

while True:
    schedule.run_pending()
    time.sleep(1)