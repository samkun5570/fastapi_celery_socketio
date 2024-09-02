from celery_app import app
import time

# @app.task(bind=True)
# @shared_task
@app.task(name="long_running_task", bind=True, max_retries=3, default_retry_delay=300)
def long_running_task(self, duration):
    for i in range(duration):
        time.sleep(1)  # Simulate a long-running task
        self.update_state(state='PROGRESS', meta={'current': i, 'total': duration})
    return {'status': 'Task completed!', 'result': 42}