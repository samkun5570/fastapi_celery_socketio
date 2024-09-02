from celery import Celery
import time

app = Celery(
    'celery_app',
    broker_url='redis://127.0.0.1:6379',  # Change this if you're using RabbitMQ or another broker
    result_backend='redis://127.0.0.1:6379',  # Using Redis as the result backend,
    result_expires=3600,
)

app.conf.update(
    result_backend='redis://127.0.0.1:6379',
    result_expires=36000,
)


# @app.task(bind=True)
# @shared_task
@app.task(name="long_running_task", bind=True, max_retries=3, default_retry_delay=300)
def long_running_task(self, duration):
    for i in range(duration):
        time.sleep(1)  # Simulate  long-running task
        self.update_state(state='PROGRESS', meta={'current': i, 'total': duration})
    return {'status': 'Task completed!', 'result': 42}


