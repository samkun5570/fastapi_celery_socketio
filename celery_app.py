from celery import Celery
import time
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Celery(
    'celery_app',
    broker_url=os.getenv("BROKER_URL"),  
    result_backend=os.getenv("RESULT_BACKEND"),  
    result_expires=os.getenv("RESULT_EXPIRES"),
)

# app.conf.update(
#     result_backend='redis://127.0.0.1:6379',
#     result_expires=36000,
# )


# @app.task(bind=True)
# @shared_task
@app.task(name="long_running_task", bind=True, max_retries=3, default_retry_delay=300)
def long_running_task(self, duration):
    for i in range(duration):
        time.sleep(1)  # Simulate  long-running task
        self.update_state(state='PROGRESS', meta={'current': i, 'total': duration})
    return {'status': 'Task completed!', 'result': 42}


