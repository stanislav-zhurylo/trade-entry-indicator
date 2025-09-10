import asyncio

def __get_event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop;

def handle_task_result(task, success_handler, failure_handler):
    try:
        success_handler(task.result())
    except RuntimeError:
        failure_handler()

def run_until_complete(method_name):
    loop = __get_event_loop()
    loop.run_until_complete(method_name())