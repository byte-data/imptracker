import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from traceback import format_exception

from django.tasks.base import TaskError, TaskResult, TaskResultStatus
from django.tasks.backends.base import BaseTaskBackend
from django.tasks.signals import task_enqueued, task_finished, task_started
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.json import normalize_json

logger = logging.getLogger(__name__)


_executor = None
_executor_lock = threading.Lock()


def _get_executor(max_workers: int) -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="django-task")
        return _executor


class ThreadedBackend(BaseTaskBackend):
    """A minimal in-process task backend that executes tasks in a thread pool.

    Notes:
    - Results are not persisted and can't be retrieved across processes.
    - Suitable for lightweight background work like sending emails.
    """

    supports_async_task = True

    def _execute_task(self, task_result: TaskResult) -> None:
        object.__setattr__(task_result, "enqueued_at", timezone.now())
        task_enqueued.send(type(self), task_result=task_result)

        task = task_result.task
        task_start_time = timezone.now()
        object.__setattr__(task_result, "status", TaskResultStatus.RUNNING)
        object.__setattr__(task_result, "started_at", task_start_time)
        object.__setattr__(task_result, "last_attempted_at", task_start_time)
        task_result.worker_ids.append(get_random_string(12))
        task_started.send(sender=type(self), task_result=task_result)

        try:
            if task.takes_context:
                from django.tasks.base import TaskContext

                raw_return_value = task.call(
                    TaskContext(task_result=task_result),
                    *task_result.args,
                    **task_result.kwargs,
                )
            else:
                raw_return_value = task.call(*task_result.args, **task_result.kwargs)

            object.__setattr__(
                task_result,
                "_return_value",
                normalize_json(raw_return_value),
            )
        except KeyboardInterrupt:
            raise
        except BaseException as e:
            object.__setattr__(task_result, "finished_at", timezone.now())
            exception_type = type(e)
            task_result.errors.append(
                TaskError(
                    exception_class_path=f"{exception_type.__module__}.{exception_type.__qualname__}",
                    traceback="".join(format_exception(e)),
                )
            )
            object.__setattr__(task_result, "status", TaskResultStatus.FAILED)
            task_finished.send(type(self), task_result=task_result)
            logger.exception("Task %s failed", task.name)
        else:
            object.__setattr__(task_result, "finished_at", timezone.now())
            object.__setattr__(task_result, "status", TaskResultStatus.SUCCESSFUL)
            task_finished.send(type(self), task_result=task_result)

    def enqueue(self, task, args, kwargs):
        self.validate_task(task)

        task_result = TaskResult(
            task=task,
            id=get_random_string(32),
            status=TaskResultStatus.READY,
            enqueued_at=None,
            started_at=None,
            last_attempted_at=None,
            finished_at=None,
            args=list(args),
            kwargs=dict(kwargs),
            backend=self.alias,
            errors=[],
            worker_ids=[],
        )

        max_workers = int(self.options.get("MAX_WORKERS", 4))
        executor = _get_executor(max_workers=max_workers)
        executor.submit(self._execute_task, task_result)

        return task_result
