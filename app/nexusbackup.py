import asyncio
from websockets import serve
import time, sys, os, glob
import requests
from requests.auth import HTTPBasicAuth
import time, ciso8601


def delete_existing_backups():
    files = glob.glob(backup_dir+'/*')
    for f in files:
        print("attempting to delete file "+f,flush=True)
        try:
            os.unlink(f)
        except OSError as e:
            print("Error: %s %s" % (f,e.strerror))
    return "Deleted files..."

def get_last_backup_run()
    response = requests.get(nexus_svc_url+"/service/rest/v1/tasks/"+task_id, \
        auth = HTTPBasicAuth(nexus_username, nexus_password))
    if response.status_code in 200:
        print("initial get response content is:",flush=True)
        answer=response.json()
        print(answer)
        last_run=answer["lastRun"]

        print("answer.lastRun " + answer["lastRun"])




def starting_backup():
    response = requests.post(nexus_svc_url+"/service/rest/v1/tasks/" + task_id + "/run", \
       auth = HTTPBasicAuth(nexus_username, nexus_password))
    if response.status_code in (200,204):
        reply="Backup Task Successfully started..."
    else:
        reply="Error starting task, status was "+str(response.status_code)
    return reply

def waiting_backup():
    task_finished=False
    while not task_finished:
        response = requests.get(nexus_svc_url+"/service/rest/v1/tasks/"+task_id, \
            auth = HTTPBasicAuth(nexus_username, nexus_password))
        print("response content is:",flush=True)
        answer=response.json()
        print(answer)
        print("answer.currentState " + answer["currentState"])

        time.sleep(2)





    return "Waiting for backup to complete"

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
            backupdetails=starting_backup()
            await websocket.send(backupdetails)
            backupdetails=waiting_backup()
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
nexus_svc_hostname=os.environ.get('NEXUS_SERVICE_HOST')
nexus_svc_port=os.environ.get('NEXUS_SERVICE_PORT_WEB')
nexus_svc_url="http://"+nexus_svc_hostname+":"+nexus_svc_port

asyncio.run(main())
