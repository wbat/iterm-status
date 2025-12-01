"""Background task runner using asyncio with TTL-based scheduling."""

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, Optional, Set

from .logging import setup_logging

logger = setup_logging()


class ScheduledTask:
    """A scheduled task with TTL and metadata."""
    
    def __init__(
        self,
        task_id: str,
        coro: Callable[[], Awaitable[Any]],
        ttl_seconds: float,
        last_run: Optional[float] = None
    ):
        self.task_id = task_id
        self.coro = coro
        self.ttl_seconds = ttl_seconds
        self.last_run = last_run or 0
        self.is_running = False
        self.error_count = 0
        self.last_error: Optional[Exception] = None
    
    def should_run(self) -> bool:
        """Check if task should run based on TTL."""
        if self.is_running:
            return False
        return time.time() - self.last_run >= self.ttl_seconds
    
    def time_until_next_run(self) -> float:
        """Get seconds until next scheduled run."""
        elapsed = time.time() - self.last_run
        return max(0, self.ttl_seconds - elapsed)


class Scheduler:
    """Background task scheduler with TTL-based refresh scheduling."""
    
    def __init__(self):
        self._tasks: Dict[str, ScheduledTask] = {}
        self._running_tasks: Set[asyncio.Task] = set()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Scheduler started")
    
    async def stop(self) -> None:
        """Stop the scheduler and cancel all tasks."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all running tasks
        async with self._lock:
            for task in list(self._running_tasks):
                task.cancel()
            
            # Wait for tasks to complete cancellation
            if self._running_tasks:
                await asyncio.gather(*self._running_tasks, return_exceptions=True)
                self._running_tasks.clear()
        
        logger.info("Scheduler stopped")
    
    async def register(
        self,
        task_id: str,
        coro: Callable[[], Awaitable[Any]],
        ttl_seconds: float
    ) -> None:
        """Register a task to be scheduled.
        
        Args:
            task_id: Unique identifier for the task
            coro: Async coroutine to run
            ttl_seconds: Time to live - task will run when TTL expires
        """
        async with self._lock:
            self._tasks[task_id] = ScheduledTask(task_id, coro, ttl_seconds)
            logger.debug(f"Registered task: {task_id} (TTL: {ttl_seconds}s)")
    
    async def unregister(self, task_id: str) -> None:
        """Unregister a task.
        
        Args:
            task_id: Task identifier to remove
        """
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.debug(f"Unregistered task: {task_id}")
    
    async def trigger(self, task_id: str) -> None:
        """Manually trigger a task to run immediately.
        
        Args:
            task_id: Task identifier to trigger
        """
        async with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.last_run = 0  # Force immediate run
                logger.debug(f"Triggered task: {task_id}")
    
    async def _run_task(self, task: ScheduledTask) -> None:
        """Run a single task with error handling.
        
        Args:
            task: Task to run
        """
        task.is_running = True
        start_time = time.time()
        
        try:
            await task.coro()
            task.error_count = 0
            task.last_error = None
        except asyncio.CancelledError:
            raise
        except Exception as e:
            task.error_count += 1
            task.last_error = e
            logger.warning(f"Task {task.task_id} failed: {e}", exc_info=True)
        finally:
            task.is_running = False
            task.last_run = time.time()
            elapsed = task.last_run - start_time
            logger.debug(f"Task {task.task_id} completed in {elapsed:.3f}s")
    
    async def _cleanup_loop(self) -> None:
        """Main cleanup loop that runs scheduled tasks."""
        while self._running:
            try:
                await self._process_tasks()
                await asyncio.sleep(0.5)  # Check every 500ms
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_tasks(self) -> None:
        """Process all tasks that are due to run."""
        async with self._lock:
            tasks_to_run = [
                task for task in self._tasks.values()
                if task.should_run()
            ]
        
        # Run tasks concurrently (but limit concurrency)
        if tasks_to_run:
            # Create tasks for execution
            async with self._lock:
                for task in tasks_to_run:
                    if not task.is_running:
                        async_task = asyncio.create_task(self._run_task(task))
                        self._running_tasks.add(async_task)
                        
                        # Clean up completed tasks
                        async_task.add_done_callback(self._running_tasks.discard)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Dictionary with task status or None if not found
        """
        task = self._tasks.get(task_id)
        if task is None:
            return None
        
        return {
            "task_id": task.task_id,
            "is_running": task.is_running,
            "last_run": task.last_run,
            "time_until_next": task.time_until_next_run(),
            "error_count": task.error_count,
            "last_error": str(task.last_error) if task.last_error else None,
        }
    
    def get_all_task_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all tasks.
        
        Returns:
            Dictionary mapping task_id to status
        """
        return {
            task_id: self.get_task_status(task_id)
            for task_id in self._tasks.keys()
        }
