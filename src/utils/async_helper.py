"""
Async Helper Utilities for handling event loops safely
"""

import asyncio
import concurrent.futures
import threading
import logging
from typing import Any, Coroutine, Optional

logger = logging.getLogger(__name__)


class AsyncHelper:
    """Thread-safe async execution helper"""
    
    _thread_pool = None
    _lock = threading.Lock()
    
    @classmethod
    def get_thread_pool(cls) -> concurrent.futures.ThreadPoolExecutor:
        """Get or create thread pool for async execution"""
        if cls._thread_pool is None:
            with cls._lock:
                if cls._thread_pool is None:
                    cls._thread_pool = concurrent.futures.ThreadPoolExecutor(
                        max_workers=5,
                        thread_name_prefix="async_helper"
                    )
        return cls._thread_pool
    
    @classmethod
    def cleanup(cls):
        """Cleanup thread pool"""
        if cls._thread_pool:
            with cls._lock:
                if cls._thread_pool:
                    cls._thread_pool.shutdown(wait=True)
                    cls._thread_pool = None

    @staticmethod
    def run_async_safe(coro: Coroutine, timeout: float = 30.0) -> Any:
        """
        Safely run async coroutine in sync context
        
        This method creates a new event loop in a separate thread to avoid
        conflicts with existing event loops.
        """
        def run_in_thread():
            """Execute coroutine in new thread with new event loop"""
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(coro)
            except Exception as e:
                logger.error(f"Error in async execution: {e}")
                raise
            finally:
                try:
                    # Cancel all pending tasks
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        for task in pending:
                            task.cancel()
                        
                        # Wait for tasks to complete cancellation
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                except Exception as cleanup_error:
                    logger.warning(f"Error during task cleanup: {cleanup_error}")
                finally:
                    try:
                        loop.close()
                    except Exception as loop_error:
                        logger.warning(f"Error closing event loop: {loop_error}")
        
        # Execute in thread pool
        executor = AsyncHelper.get_thread_pool()
        try:
            future = executor.submit(run_in_thread)
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.error(f"Async operation timed out after {timeout} seconds")
            raise Exception(f"Database operation timed out after {timeout}s")
        except Exception as e:
            logger.error(f"Error in async helper: {e}")
            raise


def run_async_safe(coro: Coroutine, timeout: float = 30.0) -> Any:
    """Convenience function for safe async execution"""
    return AsyncHelper.run_async_safe(coro, timeout)


# Cleanup on module exit
import atexit
atexit.register(AsyncHelper.cleanup)
