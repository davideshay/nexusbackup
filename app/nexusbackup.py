import asyncio
from websockets import serve
import time, sys, os, glob


def delete_existing_backups():
    print("backup dir is "+backup_dir)
    files = glob.glob(backup_dir+'/*')
    for f in files:
        print("attempting to delete file "+f,flush=True)
        try:
            f.unlink()
        except OSError as e:
            print("Error: %s %s" % (f,e.strerror))
    return "Deleted files..."

def starting_backup():
    return "Started backup"

def waiting_backup():
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
    async with serve(backup, "0.0.0.0", 80):
        await asyncio.Future()  # run forever


backup_dir=os.environ.get('BACKUPDIR')


asyncio.run(main())
