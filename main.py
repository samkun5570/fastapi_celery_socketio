from fastapi import FastAPI, WebSocket,APIRouter,Request,HTTPException
from fastapi.responses import HTMLResponse
# from celery.result import AsyncResult
import socketio
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

# from task import long_running_task
from celery_app import app as cel_app,long_running_task

logging.basicConfig(level=logging.DEBUG)

# Initialize Socket.IO server
# sio = socketio.AsyncServer(async_mode='asgi')
sio=socketio.AsyncServer(cors_allowed_origins=[],async_mode='asgi') # keep cors_allowed_origins=[] if cors has to be controlled by the application framework

app = FastAPI()

# app.add_middleware(BaseHTTPMiddleware, dispatch=ASGIApp(sio))


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing; adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory="templates")
general_pages_router = APIRouter()
# Attach the Socket.IO server to FastAPI
sio_app = socketio.ASGIApp(sio)
app.mount('/socket.io', sio_app)

@general_pages_router.get("/")
async def home(request: Request):
	return templates.TemplateResponse("general_pages/homepage.html",{"request":request})

app.include_router(general_pages_router)
sid_task_map = {}

@app.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = cel_app.AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return result


@app.post("/start-task/")
async def start_task(request: Request):
    try:    
        data = await request.json()
        duration = int(data.get("duration"))
        cel_app.autodiscover_tasks()
        # if not isinstance(duration, int):
        #     raise HTTPException(status_code=422, detail="Duration must be an integer")
        # Start the Celery task
        print(duration)

        task = long_running_task.delay(duration)
        # print('tasks : ',cel_app.tasks.keys())
        result = cel_app.AsyncResult(task.id)
        if not result.ready():  # If the task is not completed, assume it is valid
            logging.info(f"Task {task.id} started successfully")
            return {"task_id": task.id}
        else:
            logging.error("Task could not be processed")
            raise HTTPException(status_code=500, detail="Task could not be processed")
     
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    sid_task_map[sid] = {}

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    if sid in sid_task_map:
        del sid_task_map[sid]

@sio.on("track_task")
async def track_task(sid, task_id):
    task_result = AsyncResult(task_id)

    while not task_result.ready():
        # Retrieve task state and send updates
        state = task_result.state
        info = task_result.info or {}
        print("task_status", {"state": state, "info": info}, room=sid)
        await sio.emit("task_status", {"state": state, "info": info}, room=sid)
        await sio.sleep(1)  # Check status every second

    # Send the final result
    final_result = task_result.result
    print("task_status", {"state": "COMPLETED", "result": final_result}, room=sid)
    await sio.emit("task_status", {"state": "COMPLETED", "result": final_result}, room=sid)

# if __name__ == '__main__':
#     uvicorn.run('main:app',
#         host='127.0.0.1',  # Replace with the desired IP address or '0.0.0.0' for all interfaces
#         port=8000,  # Replace with the desired port number
#         reload=True
#         )
