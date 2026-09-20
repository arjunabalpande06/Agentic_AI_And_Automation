import os
import sys
import gradio as gr
from fastapi import FastAPI

# Ensure repository root and FLEXI_CA_3 directory are in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
FLEXI_DIR = os.path.join(PROJECT_ROOT, "FLEXI_CA_3")

for path in [PROJECT_ROOT, FLEXI_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from FLEXI_CA_3.app import app as gradio_app
    from FLEXI_CA_3.reminder import check_deadlines
except ImportError:
    from app import app as gradio_app
    from reminder import check_deadlines

# Create base FastAPI app
server = FastAPI()


@server.get("/api/health")
async def health():
    return {"status": "ok", "service": "Student Deadline Reminder Automation"}


@server.get("/api/check-deadlines")
async def trigger_check_deadlines():
    try:
        await check_deadlines()
        return {"status": "success", "message": "Deadline check completed successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Mount Gradio app properly to initialize frontend config and templates
app = gr.mount_gradio_app(server, gradio_app, path="/")
