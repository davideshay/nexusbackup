import asyncio
from websockets import serve
import time, sys, os, glob
import requests
from requests.auth import HTTPBasicAuth
import time
from datetime import datetime


def delete_existing_backups():
    global backup_dir
    files = glob.glob(backup_dir+'/*')
    for f in files:
        print("attempting to delete file "+f,flush=True)
        try:
            os.unlink(f)
        except OSError as e:
            print("Error: %s %s" % (f,e.strerror))
    return "Deleted files..."

def get_last_backup_run():
    global nexus_svc_url
    global task_id
    global nexus_username
    global nexus_password
    response = requests.get(nexus_svc_url+"/service/rest/v1/tasks/"+task_id, \
        auth = HTTPBasicAuth(nexus_username, nexus_password))
    last_run_date = None
    if response.status_code == 200:
        answer=response.json()
        last_run_str=answer["lastRun"]
        last_run_date=datetime.fromisoformat(last_run_str)
    return last_run_date

def starting_backup():
    global nexus_svc_url
    global task_id
    global nexus_username
    global nexus_password
    response = requests.post(nexus_svc_url+"/service/rest/v1/tasks/" + task_id + "/run", \
       auth = HTTPBasicAuth(nexus_username, nexus_password))
    if response.status_code in (200,204):
        reply="Backup Task Successfully started..."
    else:
        reply="Error starting task, status was "+str(response.status_code)
    return reply

def waiting_backup(initial_last_run_date):
    global nexus_svc_url
    global task_id
    global nexus_username
    global nexus_password
    task_finished=False
    current_last_run_date=None
    while not task_finished:
        response = requests.get(nexus_svc_url+"/service/rest/v1/tasks/"+task_id, \
            auth = HTTPBasicAuth(nexus_username, nexus_password))
        if response.status_code == 200:
            answer=response.json()
            if answer["currentState"]=="WAITING":
                current_last_run_date=datetime.fromisoformat(answer["lastRun"])
                if  current_last_run_date > initial_last_run_date:
                    task_finished=True
        time.sleep(2)
    reply="Backup completed on "+str(current_last_run_date)
    return reply

def bundle_files():
    return "Bundling files"

def rsync_files():
    return "Copying backup files"

def remove_files():
    return "Cleaning up"


async def backup(websocket):
    async for message in websocket:
        if message=="start":
            backupdetails=delete_existing_backups()
            await websocket.send(backupdetails)
            initial_last_run_date=get_last_backup_run()
            backupdetails="Last run  of backup was "+str(initial_last_run_date)
            await websocket.send(backupdetails)
            backupdetails=starting_backup()
            await websocket.send(backupdetails)
            backupdetails=waiting_backup(initial_last_run_date)
            await websocket.send(backupdetails)
            backupdetails=bundle_files()
            await websocket.send(backupdetails)
            backupdetails=rsync_files()
            await websocket.send(backupdetails)
            backupdetails=remove_files()
            await websocket.send(backupdetails)
            backupdetails="end"
            await websocket.send(backupdetails)


async def main():
    async with serve(backup, "0.0.0.0", 8000):
        await asyncio.Future()  # run forever


backup_dir=os.environ.get('BACKUPDIR')
task_id=os.environ.get('TASKID')
nexus_username=os.environ.get('NEXUS_USERNAME')
nexus_password=os.environ.get('NEXUS_PASSWORD')
nexus_svc_hostname=os.environ.get('NEXUS_SVC_HOSTNAME')
nexus_svc_port=os.environ.get('NEXUS_SVC_PORT')
print("hostname is "+nexus_svc_hostname)
print("port is "+nexus_svc_port)

nexus_svc_url="http://"+nexus_svc_hostname+":"+nexus_svc_port
print("url is "+nexus_svc_url)


asyncio.run(main())
