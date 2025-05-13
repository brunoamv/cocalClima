#!/usr/bin/env python3
"""
Cria uma nova transmissão YouTube e a vincula
ao stream RTMP fixo (stream key yx67‑vfxc‑q2vb‑4rkb‑402d).
Atualiza myproject/core/views.py com o YOUTUBE_VIDEO_ID.
"""

import sys
sys.path.insert(0, "/home/bruno/Desktop/Mega/Curso/Django/App/cocalTempo2/myvenv/lib/python3.12/site-packages")

import os
import logging
from datetime import datetime, timedelta, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

# --- Caminhos ----------------------------------------------------------
BASE_DIR = "/home/bruno/Desktop/Mega/Curso/Django/App/cocalTempo2"
SCRIPT_NAME = os.path.basename(__file__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"{os.path.splitext(SCRIPT_NAME)[0]}_log_{LOG_TIME}.log")




CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "youtube", "client_secret.json")
TOKEN_FILE         = os.path.join(BASE_DIR, "youtube", "token.json")
VIEWS_FILE         = os.path.join(BASE_DIR, "myproject", "core", "views.py")

# --- Configuração de logging ------------------------------------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger()

# --- Constantes --------------------------------------------------------
SCOPES          = ["https://www.googleapis.com/auth/youtube"]
FIXED_STREAMKEY = "yx67-vfxc-q2vb-4rkb-402d"

# ----------------------------------------------------------------------
def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

# ----------------------------------------------------------------------
def find_fixed_stream(youtube):
    req = youtube.liveStreams().list(part="snippet,cdn", mine=True, maxResults=50)
    while req:
        res = req.execute()
        for item in res.get("items", []):
            info = item["cdn"]["ingestionInfo"]
            if info["streamName"] == FIXED_STREAMKEY:
                return item["id"], info["ingestionAddress"]
        req = youtube.liveStreams().list_next(req, res)

    stream = youtube.liveStreams().insert(
        part="snippet,cdn",
        body={
            "snippet": {"title": "Stream RTMP fixo do ClimaCocal"},
            "cdn": {
                "format": "1080p",
                "resolution": "1080p",
                "frameRate": 60,
                "ingestionType": "rtmp"
            }
        }
    ).execute()

    youtube.liveStreams().update(
        part="cdn",
        body={
            "id": stream["id"],
            "cdn": {**stream["cdn"], "ingestionInfo": {
                **stream["cdn"]["ingestionInfo"],
                "streamName": FIXED_STREAMKEY
            }}
        }
    ).execute()

    info = stream["cdn"]["ingestionInfo"]
    return stream["id"], info["ingestionAddress"]

# ----------------------------------------------------------------------
def delete_active_broadcasts(youtube):
    req = youtube.liveBroadcasts().list(part="id,status", mine=True, maxResults=50)
    while req:
        res = req.execute()
        for item in res.get("items", []):
            status = item["status"].get("lifeCycleStatus", "")
            if status in ("live", "created", "ready"):
                bid = item["id"]
                youtube.liveBroadcasts().delete(id=bid).execute()
                logger.info(f"Transmissão {bid} encerrada.")
        req = youtube.liveBroadcasts().list_next(req, res)

# ----------------------------------------------------------------------
def create_new_broadcast(youtube, stream_id):
    now = datetime.now(timezone.utc)
    start = (now + timedelta(minutes=2)).isoformat()
    end   = (now + timedelta(hours=1)).isoformat()

    broadcast = youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {
                "title": f"Transmissão ClimaCocal {now:%Y-%m-%d}",
                "scheduledStartTime": start,
                "scheduledEndTime":   end
            },
            "status": {"privacyStatus": "unlisted"},
            "contentDetails": {"enableAutoStart": True, "enableAutoStop": True}
        }
    ).execute()

    youtube.liveBroadcasts().bind(
        part="id,contentDetails", id=broadcast["id"], streamId=stream_id
    ).execute()

    return broadcast["id"]

# ----------------------------------------------------------------------
def update_views_py(video_id):
    updated = False
    with open(VIEWS_FILE, "r") as f:
        lines = f.readlines()

    with open(VIEWS_FILE, "w") as f:
        for line in lines:
            if line.strip().startswith("YOUTUBE_VIDEO_ID"):
                f.write(f'YOUTUBE_VIDEO_ID = "{video_id}"\n')
                updated = True
            else:
                f.write(line)
        if not updated:
            f.write(f'\nYOUTUBE_VIDEO_ID = "{video_id}"\n')
    logger.info(f"views.py atualizado com YOUTUBE_VIDEO_ID = {video_id}")

# ----------------------------------------------------------------------
def git_commit():
    os.system(f"cd {BASE_DIR} && git add {VIEWS_FILE} && "
              "git commit -m 'Atualiza YOUTUBE_VIDEO_ID automaticamente' && "
              "git push")
    logger.info("Commit e push feitos com sucesso.")

# ----------------------------- MAIN -----------------------------------
if __name__ == "__main__":
    try:
        logger.info("==== Início do script de automação YouTube ====")

        yt = get_authenticated_service()
        delete_active_broadcasts(yt)
        stream_id, rtmp_url = find_fixed_stream(yt)
        broadcast_id = create_new_broadcast(yt, stream_id)

        update_views_py(broadcast_id)
        git_commit()

        logger.info("Broadcast ID : %s", broadcast_id)
        logger.info("RTMP URL     : %s/%s", rtmp_url, FIXED_STREAMKEY)
        logger.info("==== Fim do script com sucesso ====")

    except Exception as e:
        logger.exception("Erro durante a execução do script:")
        raise
