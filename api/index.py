import os
import sys

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

# Gradio's underlying ASGI application is stored in app.app
app = gradio_app.app


# Add serverless API endpoints (for health check and Vercel Cron)
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Student Deadline Reminder Automation"}


@app.get("/api/check-deadlines")
async def trigger_check_deadlines():
    try:
        await check_deadlines()
        return {"status": "success", "message": "Deadline check completed successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
