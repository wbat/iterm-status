"""Safe async subprocess wrapper with timeout and output limits."""

import asyncio
import shlex
from typing import Optional, Tuple

from ..core.logging import setup_logging

logger = setup_logging()

# Default limits
DEFAULT_TIMEOUT = 5.0  # seconds
DEFAULT_MAX_OUTPUT = 1024 * 1024  # 1MB


async def run_command(
    command: str,
    timeout: float = DEFAULT_TIMEOUT,
    max_output: int = DEFAULT_MAX_OUTPUT,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    shell: bool = False
) -> Tuple[int, str, str]:
    """Run a command asynchronously with timeout and output limits.
    
    Args:
        command: Command to run (string or list)
        timeout: Maximum execution time in seconds
        max_output: Maximum output size in bytes
        cwd: Working directory
        env: Environment variables
        shell: Whether to use shell execution
        
    Returns:
        Tuple of (returncode, stdout, stderr)
        
    Raises:
        asyncio.TimeoutError: If command exceeds timeout
        ValueError: If output exceeds max_output
    """
    # Parse command if string
    if isinstance(command, str):
        if shell:
            cmd = command
        else:
            cmd = shlex.split(command)
    else:
        cmd = command
    
    try:
        # Create process
        process = await asyncio.create_subprocess_exec(
            *cmd if not shell else cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            shell=shell
        )
        
        # Read output with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Kill process on timeout
            process.kill()
            await process.wait()
            raise asyncio.TimeoutError(f"Command exceeded timeout of {timeout}s")
        
        # Check output size
        if len(stdout) > max_output:
            logger.warning(f"Command output exceeded {max_output} bytes, truncating")
            stdout = stdout[:max_output]
        
        if len(stderr) > max_output:
            logger.warning(f"Command stderr exceeded {max_output} bytes, truncating")
            stderr = stderr[:max_output]
        
        # Decode output
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        
        return process.returncode, stdout_text, stderr_text
    
    except FileNotFoundError as e:
        logger.warning(f"Command not found: {command}")
        return 127, "", str(e)
    except Exception as e:
        logger.error(f"Error running command {command}: {e}", exc_info=True)
        return 1, "", str(e)


async def run_command_safe(
    command: str,
    timeout: float = DEFAULT_TIMEOUT,
    max_output: int = DEFAULT_MAX_OUTPUT,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    default: str = ""
) -> str:
    """Run a command and return stdout, or default on error.
    
    This is a convenience wrapper that returns stdout on success
    or a default value on any error.
    
    Args:
        command: Command to run
        timeout: Maximum execution time
        max_output: Maximum output size
        cwd: Working directory
        env: Environment variables
        default: Default value to return on error
        
    Returns:
        Command stdout or default value
    """
    try:
        returncode, stdout, stderr = await run_command(
            command, timeout, max_output, cwd, env
        )
        if returncode == 0:
            return stdout
        else:
            logger.debug(f"Command failed with returncode {returncode}: {stderr}")
            return default
    except Exception as e:
        logger.debug(f"Command error: {e}")
        return default


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH.
    
    Args:
        command: Command name to check
        
    Returns:
        True if command exists, False otherwise
    """
    import shutil
    return shutil.which(command) is not None
