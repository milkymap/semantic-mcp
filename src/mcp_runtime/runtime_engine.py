import json
import asyncio
from uuid import uuid4
from hashlib import sha256
from typing import Self, Dict, Optional, Set, Tuple, List, AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager, suppress

import zmq
import zmq.asyncio as azmq

from mcp import StdioServerParameters, ClientSession, stdio_client
from mcp.client.streamable_http import streamablehttp_client

from .settings import RuntimeSettings
from .services.discovery_client import DiscoveryClient
from .services.content_manager import ContentManager
from .models import McpStartupConfig
from .log import logger


class RuntimeEngine:

    def __init__(self, settings: RuntimeSettings):
        self.settings = settings

    async def __aenter__(self) -> Self:
        self.resources_manager = AsyncExitStack()

        self.discovery_client = await self.resources_manager.enter_async_context(
            DiscoveryClient(
                base_url=self.settings.DISCOVERY_URL,
                api_key=self.settings.DISCOVERY_API_KEY,
                encryption_key=self.settings.DISCOVERY_ENCRYPTION_KEY
            )
        )

        self.mcp_server_tasks: Dict[str, asyncio.Task] = {}
        self.subscriber_tasks: Set[asyncio.Task] = set()
        self.background_tasks: Dict[str, asyncio.Task] = {}

        self.ctx = azmq.Context()
        self.priority_queue = asyncio.PriorityQueue(
            maxsize=self.settings.BACKGROUND_QUEUE_SIZE
        )

        content_manager = ContentManager(
            storage_path=self.settings.TOOL_OFFLOADED_DATA_PATH,
            openai_api_key=self.settings.OPENAI_API_KEY,
            max_tokens=self.settings.MAX_RESULT_TOKENS,
            describe_images=self.settings.DESCRIBE_IMAGES,
            vision_model=self.settings.VISION_MODEL_NAME,
        )
        self.content_manager = await self.resources_manager.enter_async_context(content_manager)

        for _ in range(self.settings.BACKGROUND_QUEUE_MAX_SUBSCRIBERS):
            task = asyncio.create_task(self._subscriber())
            self.subscriber_tasks.add(task)

        logger.info("RuntimeEngine initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Exception in RuntimeEngine: {exc_val}")

        cancelled_tasks: List[asyncio.Task] = []
        for server_name, task in self.mcp_server_tasks.items():
            logger.info(f"Cancelling server task: {server_name}")
            if not task.done():
                task.cancel()
                cancelled_tasks.append(task)
        await asyncio.gather(*cancelled_tasks, return_exceptions=True)

        cancelled_tasks.clear()
        for task in self.subscriber_tasks:
            if not task.done():
                task.cancel()
                cancelled_tasks.append(task)
        await asyncio.gather(*cancelled_tasks, return_exceptions=True)

        cancelled_tasks.clear()
        for task_id, task in self.background_tasks.items():
            if not task.done():
                task.cancel()
                cancelled_tasks.append(task)
        await asyncio.gather(*cancelled_tasks, return_exceptions=True)

        self.ctx.term()
        await self.resources_manager.aclose()
        logger.info("RuntimeEngine shutdown complete")

    @asynccontextmanager
    async def _create_socket(self, socket_type: int, socket_method: str, addr: str) -> AsyncGenerator[azmq.Socket, None]:
        socket = self.ctx.socket(socket_type)
        try:
            if socket_method == "bind":
                socket.bind(addr)
            elif socket_method == "connect":
                socket.connect(addr)
            yield socket
        finally:
            socket.close(linger=0)

    async def _subscriber(self):
        logger.info("Starting background task subscriber")
        while True:
            try:
                task = await self.priority_queue.get()
                priority, (server_name, tool_name, arguments, timeout, task_id) = task
                logger.info(f"Processing task {task_id}: {tool_name}@{server_name}")
                task_handler = asyncio.create_task(
                    self._handle_tool_call(
                        server_name=server_name,
                        tool_name=tool_name,
                        arguments=arguments,
                        timeout=timeout
                    )
                )
                self.background_tasks[task_id] = task_handler
                with suppress(Exception):
                    await task_handler
                self.priority_queue.task_done()
            except asyncio.CancelledError:
                break

    async def _call_mcp_tool(self, session: ClientSession, tool_name: str, tool_arguments: Dict, timeout: float = 60) -> bytes:
        try:
            async with asyncio.timeout(delay=timeout):
                result = await session.call_tool(name=tool_name, arguments=tool_arguments)
                content = []
                for block in result.content:
                    block_dict = block.model_dump()
                    block_dict.pop("annotations", None)
                    block_dict.pop("meta", None)
                    content.append(block_dict)
                return json.dumps({"status": True, "content": content}).encode('utf-8')
        except TimeoutError:
            logger.error(f"Timeout: {tool_name}")
            return json.dumps({"status": False, "error_message": "Tool execution timed out"}).encode('utf-8')
        except Exception as e:
            logger.error(f"Error: {tool_name} - {e}")
            return json.dumps({"status": False, "error_message": str(e)}).encode('utf-8')

    async def _background_mcp_server(self, server_name: str, config: McpStartupConfig):
        async with AsyncExitStack() as stack:
            if config.transport == "http":
                logger.info(f"[{server_name}] Connecting via HTTP: {config.url}")
                transport = await stack.enter_async_context(
                    streamablehttp_client(config.url, headers=config.headers or None)
                )
                read, write, _ = transport
            else:
                logger.info(f"[{server_name}] Starting via stdio: {config.command}")
                # Merge config env with npm-silencing variables to prevent
                # npm/npx from polluting stdout with non-JSON-RPC messages
                server_env = {
                    **config.env,
                    "NPM_CONFIG_LOGLEVEL": "silent",
                    "npm_config_progress": "false",
                    "NO_UPDATE_NOTIFIER": "true",
                }
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=server_env
                )
                transport = await stack.enter_async_context(stdio_client(server=server_params))
                read, write = transport

            session = await stack.enter_async_context(ClientSession(read, write))
            try:
                async with asyncio.timeout(delay=config.timeout):
                    await session.initialize()
                    tools = await session.list_tools()
                    logger.info(f"[{server_name}] Connected, {len(tools.tools)} tools available")
            except TimeoutError:
                logger.error(f"[{server_name}] Connection timeout")
                raise
            except Exception as e:
                logger.error(f"[{server_name}] Connection failed: {e}")
                raise

            current_task = asyncio.current_task()
            current_task.set_name(current_task.get_name().replace("PENDING", "RUNNING"))

            server_hash = sha256(server_name.encode('utf-8')).hexdigest()
            router_socket = await stack.enter_async_context(
                self._create_socket(zmq.ROUTER, "bind", f"inproc://{server_hash}")
            )

            poller = azmq.Poller()
            poller.register(router_socket, zmq.POLLIN)

            while True:
                try:
                    events = dict(await poller.poll(timeout=self.settings.MCP_SERVER_POLLING_INTERVAL_MS))
                    if router_socket not in events or events[router_socket] != zmq.POLLIN:
                        continue

                    caller_id, _, encoded_request = await router_socket.recv_multipart()
                    request: Dict = json.loads(encoded_request.decode('utf-8'))
                    result = await self._call_mcp_tool(
                        session=session,
                        tool_name=request.get("tool_name", ""),
                        tool_arguments=request.get("tool_arguments", {}),
                        timeout=request.get("timeout", 60)
                    )
                    await router_socket.send_multipart([caller_id, b"", result])
                except asyncio.CancelledError:
                    logger.info(f"[{server_name}] Shutting down")
                    break
                except Exception as e:
                    logger.error(f"[{server_name}] Loop error: {e}")
                    break

            poller.unregister(router_socket)
            logger.info(f"[{server_name}] Shutdown complete")

    def _clear_server_task(self, task: asyncio.Task):
        task_name = task.get_name()
        parts = task_name.split("_")
        if len(parts) >= 3:
            server_name = parts[2]
            self.mcp_server_tasks.pop(server_name, None)
            logger.info(f"Cleared task: {server_name}")

    async def start_mcp_server(self, server_name: str) -> Tuple[bool, str]:
        if server_name in self.mcp_server_tasks:
            return True, f"Server '{server_name}' already running"

        try:
            config = await self.discovery_client.get_startup_config(server_name)
        except Exception as e:
            return False, f"Failed to get config for '{server_name}': {e}"

        task = asyncio.create_task(
            self._background_mcp_server(server_name=server_name, config=config)
        )
        task.set_name(f"BACKGROUND_TASK_{server_name}_PENDING")
        self.mcp_server_tasks[server_name] = task
        task.add_done_callback(self._clear_server_task)

        while not task.done():
            if "RUNNING" in task.get_name():
                return True, f"Server '{server_name}' started"
            await asyncio.sleep(0.5)

        error = str(task.exception()) if task.exception() else "Unknown error"
        return False, f"Failed to start '{server_name}': {error}"

    async def shutdown_mcp_server(self, server_name: str) -> Tuple[bool, str]:
        task = self.mcp_server_tasks.get(server_name)
        if not task:
            return True, f"Server '{server_name}' not running"

        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            return False, str(e)

        return True, f"Server '{server_name}' stopped"

    async def _handle_tool_call(self, server_name: str, tool_name: str, arguments: Optional[dict] = None, timeout: float = 60) -> List[Dict]:
        server_hash = sha256(server_name.encode('utf-8')).hexdigest()
        async with self._create_socket(zmq.DEALER, "connect", f"inproc://{server_hash}") as socket:
            await socket.send_multipart([b""], flags=zmq.SNDMORE)
            await socket.send_json({
                "tool_name": tool_name,
                "tool_arguments": arguments or {},
                "timeout": timeout
            })
            _, encoded_response = await socket.recv_multipart()
            response: Dict = json.loads(encoded_response.decode('utf-8'))
            if response["status"]:
                return response["content"]
            raise Exception(response.get("error_message", "Unknown error"))

    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[dict] = None,
        timeout: float = 60,
        priority: int = 1,
        in_background: bool = False
    ) -> List[Dict]:
        if server_name not in self.mcp_server_tasks:
            raise Exception(f"Server '{server_name}' not running")

        task = self.mcp_server_tasks[server_name]
        if "RUNNING" not in task.get_name():
            raise Exception(f"Server '{server_name}' not ready")

        if in_background:
            task_id = str(uuid4())
            await self.priority_queue.put((priority, (server_name, tool_name, arguments, timeout, task_id)))
            return [{"type": "text", "text": f"Task queued with ID: {task_id}"}]

        result = await self._handle_tool_call(server_name, tool_name, arguments, timeout)
        return await self.content_manager.process_content(result)

    async def poll_task_result(self, task_id: str) -> Tuple[bool, Optional[List[Dict]], Optional[str]]:
        task = self.background_tasks.get(task_id)
        if not task:
            return False, None, f"Task not found: {task_id}"

        if not task.done():
            return False, None, None

        try:
            result = task.result()
            del self.background_tasks[task_id]
            processed = await self.content_manager.process_content(result)
            return True, processed, None
        except Exception as e:
            del self.background_tasks[task_id]
            return False, None, str(e)

    def list_running_servers(self) -> List[str]:
        return list(self.mcp_server_tasks.keys())
