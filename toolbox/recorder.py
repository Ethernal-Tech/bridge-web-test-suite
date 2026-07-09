import json
import threading
from time import time
from requests import get
from shutil import rmtree, which
from subprocess import run
from typing import Optional
from base64 import b64decode
from os import makedirs, path
from websocket import WebSocket, create_connection
from toolbox.chrome import Chrome
from toolbox.logger import logger, logs_dir_path


class ScreenRecorder:
    def __init__(
            self,
            driver: Chrome
    ) -> None:

        self.__driver: Chrome = driver
        self.__output_path: str = path.join(logs_dir_path, "record.mp4")
        self.__frames_dir: str = f"{self.__output_path}.frames"
        self.__frame_lock: threading.Lock = threading.Lock()
        self.__frame_count: int = 0
        self.__frame_timestamps: list = []
        self.__stop_event: threading.Event = threading.Event()
        self.__watcher_thread: Optional[threading.Thread] = None
        self.__active_web_socket: Optional[WebSocket] = None
        self.__active_capture_thread: Optional[threading.Thread] = None
        self.__active_target_id: Optional[str] = None
        self.__poll_interval_seconds: float = 0.5

    def __watch(self) -> None:

        while not self.__stop_event.is_set():

            try:
                handle = self.__driver.current_window_handle
            except Exception as error:
                logger.debug(f"Could not read active window handle: {error}")
                handle = None

            if handle and handle != self.__active_target_id:
                self.__switch_target(handle)

            self.__stop_event.wait(self.__poll_interval_seconds)

        self.__stop_capture()

    def __switch_target(self, handle: str) -> None:

        logger.debug(f"Switching recording to tab {handle}")

        self.__stop_capture()

        try:

            debugger_address = self.__driver.capabilities["goog:chromeOptions"]["debuggerAddress"]

            targets = get(f"http://{debugger_address}/json").json()
            target = next((t for t in targets if t["id"] == handle), None)

            if not target:
                logger.debug(f"No CDP target found for window handle {handle}")
                return

            web_socket = create_connection(target["webSocketDebuggerUrl"])
            web_socket.send(json.dumps({
                "id": 1,
                "method": "Page.startScreencast",
                "params": {
                    "format": 
                    "png", 
                    "everyNthFrame": 1
                }
            }))

            self.__active_web_socket = web_socket
            self.__active_target_id = handle

            self.__active_capture_thread = threading.Thread(
                target=self.__capture, 
                args=(web_socket,), 
                daemon=True
            )

            self.__active_capture_thread.start()

            logger.debug(f"Recording switched to tab {handle} ({target.get('url')})")

        except Exception as e:
            # broad on purpose: this runs on every poll from the watcher thread,
            # a failed switch must not raise and kill the thread, just retry on the next poll
            logger.debug(f"Failed to switch recording to tab {handle}: {e}")

    def __stop_capture(self) -> None:

        if self.__active_web_socket:

            try:
                self.__active_web_socket.send(json.dumps({"id": -1, "method": "Page.stopScreencast"}))
            except Exception:
                pass

            try:
                self.__active_web_socket.close()
            except Exception:
                pass

        if self.__active_capture_thread:
            self.__active_capture_thread.join(timeout=5)

        self.__active_web_socket = None
        self.__active_capture_thread = None
        self.__active_target_id = None

    def __capture(self, web_socket: WebSocket) -> None:

        while True:

            try:
                data: str = web_socket.recv()
            except Exception as error:
                # the connection is only ever closed deliberately from __stop_capture(),
                # so this is the sole legitimate reason to end the loop
                logger.debug(f"Screencast connection closed: {error}")
                break

            if not data:
                continue

            try:
                message: dict = json.loads(data)
            except Exception as error:
                logger.debug(f"Failed to parse screencast message, skipping: {error}")
                continue

            if message.get("method") != "Page.screencastFrame":
                continue

            with self.__frame_lock:
                self.__frame_count += 1
                frame_number = self.__frame_count
                self.__frame_timestamps.append(time())

            try:
                with open(path.join(self.__frames_dir, f"frame_{frame_number:05d}.png"), "wb") as f:
                    f.write(b64decode(message["params"]["data"]))
            except Exception as e:
                logger.debug(f"Failed to write screencast frame {frame_number}: {e}")

            if frame_number % 50 == 0:
                logger.debug(f"Captured {frame_number} screencast frames")

            try:
                web_socket.send(json.dumps({
                    "id": frame_number + 1000,
                    "method": "Page.screencastFrameAck",
                    "params": {
                        "sessionId": message["params"]["sessionId"]
                    }
                }))
            except Exception as error:
                logger.debug(f"Failed to ack screencast frame {frame_number}: {error}")

    def __encode_video(self) -> None:

        if self.__frame_count < 2:

            logger.warning("Not enough frames captured to encode video")
            return

        concat_list_path = path.join(self.__frames_dir, "concat.txt")

        with open(concat_list_path, "w", encoding="utf-8") as f:

            for i in range(self.__frame_count - 1):

                duration = self.__frame_timestamps[i + 1] - self.__frame_timestamps[i]
                f.write(f"file 'frame_{i + 1:05d}.png'\n")
                f.write(f"duration {duration}\n")

            f.write(f"file 'frame_{self.__frame_count:05d}.png'\n")

        result = run(
            args=[
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_list_path,
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                "-pix_fmt", "yuv420p",
                self.__output_path
            ],
            capture_output=True,
            check=False
        )

        if result.returncode != 0:
            logger.warning(f"Failed to encode recording: {result.stderr.decode(errors='ignore')}")
        else:
            logger.debug("Recording encoded successfully")

    def start_recording(self) -> None:

        if not which("ffmpeg"):
            logger.warning("ffmpeg not found")
            return

        makedirs(self.__frames_dir, exist_ok=True)

        self.__watcher_thread = threading.Thread(target=self.__watch, daemon=True)
        self.__watcher_thread.start()

        logger.debug("Screen recording started")

    def stop_recording(self) -> None:

        if not self.__watcher_thread:
            return

        self.__stop_event.set()
        self.__watcher_thread.join(timeout=10)

        logger.debug(f"Screen recording stopped. {self.__frame_count} frames captured")

        try:
            self.__encode_video()
        except Exception as e:
            logger.warning(f"Failed to encode recording: {e}")
        finally:
            rmtree(self.__frames_dir, ignore_errors=True)
