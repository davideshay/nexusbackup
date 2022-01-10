import asyncio
from websockets import serve
import time, sys, os, glob, tarfile
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime


def delete_existing_backups():
    success=True
    files = glob.glob(full_backup_dir+'/*.bak')
    for f in files:
        try:
            os.unlink(f)
        except OSError as e:
            print("Error: %s %s" % (f,e.strerror),flush=True)
            success=False
    return f"I {datetime.now()} Deleted existing backup files"

def get_last_backup_run():
    response = requests.get(nexus_svc_url+"/service/rest/v1/tasks/"+task_id, \
        auth = HTTPBasicAuth(nexus_username, nexus_password))
    last_run_date = None
    if response.status_code == 200:
        answer=response.json()
        last_run_str=answer["lastRun"]
        last_run_date=datetime.fromisoformat(last_run_str)
    return last_run_date

def starting_backup():
    response = requests.post(nexus_svc_url+"/service/rest/v1/tasks/" + task_id + "/run", \
       auth = HTTPBasicAuth(nexus_username, nexus_password))
    if response.status_code in (200,204):
        reply=f"I {datetime.now()} Backup Task Successfully started..."
    else:
        reply=f"E {datetime.now()} Error starting task, status was {response.status_code}"
    return reply

def waiting_backup(initial_last_run_date):
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
    reply=f"I {datetime.now()} Backup completed"
    return reply

def tar_backup_files(backup_file_name):
    success=True
    with tarfile.open(backup_file_name,"a:") as tar:
        try:
            tar.add(full_backup_dir)
        except OSError as e:
            print(f"Error: {e.strerror}",flush=True)
            success=False
        tar.close()
    if success:
        reply=f"I {datetime.now()} Backup bundled/tar created"
    else:
        reply=f"E {datetime.now()} Error creating bundle/tar"
    return reply

def tar_blob_files(backup_file_name):
    success=True
    with tarfile.open(backup_file_name,"a:") as tar:
        try:
            tar.add(f"{blob_dir}/")
        except OSError as e:
            print(f"Error {e.strerror}",flush=True)
            success=False
        tar.close()
    if success:
        reply=f"I {datetime.now()} Blob bundled/tar appended"
    else:
        reply=f"E {datetime.now()} Error appending blob bundle"
    return reply

def tar_keystore_files(backup_file_name):
    success=True
    with tarfile.open(backup_file_name,"a:") as tar:
        try:
            tar.add(f"{id_dir}/")
        except OSError as e:
            print(f"Error {e.strerror}",flush=True)
            success=False
        tar.close()
    if success:
        reply=f"I {datetime.now()} Keystore node/id bundled/tar appended"
    else:
        reply=f"E {datetime.now()} Error appending keystore node/id"
    return reply

async def backup(websocket):
    async for message in websocket:
        if message=="start":
            backup_run_time=datetime.now().strftime('%Y%m%d-%H%M')
            backup_file_name=f"{target_dir}/nxsbackup-{backup_run_time}.tar"
            print(f"I {datetime.now()} Backup process initiated...",flush=True)
            backupdetails=delete_existing_backups()
            await websocket.send(backupdetails)
            initial_last_run_date=get_last_backup_run()
            backupdetails=f"I {datetime.now()} Last run of backup was {initial_last_run_date}"
            await websocket.send(backupdetails)
            backupdetails=starting_backup()
            await websocket.send(backupdetails)
            backupdetails=waiting_backup(initial_last_run_date)
            await websocket.send(backupdetails)
            backupdetails=tar_backup_files(backup_file_name)
            await websocket.send(backupdetails)
            backupdetails=tar_blob_files(backup_file_name)
            await websocket.send(backupdetails)
            backupdetails=tar_keystore_files(backup_file_name)
            await websocket.send(backupdetails)
            backupdetails=delete_existing_backups()
            await websocket.send(backupdetails)
            backupdetails="end"
            await websocket.send(backupdetails)
            print(f"I {datetime.now()} Backup process completed...",flush=True)

async def main():
    async with serve(backup, "0.0.0.0", 8000,ping_timeout=None,close_timeout=None):
        await asyncio.Future()  # run forever

backup_dir=os.environ.get('BACKUPDIR')
nexus_base_dir=os.environ.get('NEXUSBASEDIR')
target_dir=os.environ.get('TARGETDIR')
task_id=os.environ.get('TASKID')
nexus_username=os.environ.get('NEXUS_USERNAME')
nexus_password=os.environ.get('NEXUS_PASSWORD')
nexus_svc_hostname=os.environ.get('NEXUS_SVC_HOSTNAME')
nexus_svc_port=os.environ.get('NEXUS_SVC_PORT')
nexus_svc_url="http://"+nexus_svc_hostname+":"+nexus_svc_port
blob_dir=f"{nexus_base_dir}/blobs"
id_dir=f"{nexus_base_dir}/keystores/node"
full_backup_dir=f"{nexus_base_dir}/{backup_dir}/"

asyncio.run(main())
