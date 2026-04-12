import threading
import time
import uuid
import asyncio
import queue


class RuntimeControl:
    def __init__(self, default_throttle_ms: float = 5.0):
        self._shutdown = False
        # --- PAUSE / THROTTLE / STOP DOMAIN ---
        self._lock = threading.Lock()
        self._resume_condition = threading.Condition(self._lock)
        self._paused = False
        self._throttle_ms = max(0.0, float(default_throttle_ms))
        self._stop_requested = False

        # --- POPUP DOMAIN (another lock) ---
        self._popup_lock = threading.Lock()
        self._popup_condition = threading.Condition(self._popup_lock)
        self._pending_popups = {}  # request_id -> selected

        # GUI update queue for in-process communication (step -> backend)
        self._gui_update_queue = queue.Queue()

    def shutdown(self):
        with self._popup_condition:
            self._shutdown = True
            self._popup_condition.notify_all()

        with self._resume_condition:
            self._resume_condition.notify_all()

    # =========================================================
    # PAUSE / THROTTLE / STOP
    # =========================================================

    def set_stop_requested(self, stop_requested: bool) -> None:
        with self._lock:
            self._stop_requested = bool(stop_requested)

    def set_paused(self, paused: bool) -> None:
        with self._resume_condition:
            self._paused = bool(paused)
            if not self._paused:
                self._resume_condition.notify_all()

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    def wait_until_resumed(self) -> None:
        with self._resume_condition:
            while self._paused:
                self._resume_condition.wait(timeout=0.2)

    def set_throttle_ms(self, throttle_ms: float) -> None:
        with self._lock:
            self._throttle_ms = max(0.0, float(throttle_ms))

    def get_throttle_ms(self) -> float:
        with self._lock:
            return self._throttle_ms

    def get_throttle_seconds(self) -> float:
        return self.get_throttle_ms() / 1000.0

    def sleep_with_pause(self, delay_seconds: float) -> None:
        if delay_seconds <= 0:
            return

        end_time = time.monotonic() + delay_seconds
        while True:
            self.wait_until_resumed()
            remaining = end_time - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.05))

    def checkpoint_before_step(self, step_index: int, apply_throttle: bool = True) -> None:
        if self._stop_requested:
            raise RuntimeError("Stop requested")

        self.wait_until_resumed()
        if apply_throttle and step_index > 0:
            self.sleep_with_pause(self.get_throttle_seconds())
        self.wait_until_resumed()

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "paused": self._paused,
                "throttle_ms": self._throttle_ms,
                "stop_requested": self._stop_requested
            }

    # =========================================================
    # POPUP (lock separato)
    # =========================================================

    def show_popup(self, popup_data: dict = None) -> dict:
        request_id = str(uuid.uuid4())

        with self._popup_condition:
            self._pending_popups[request_id] = None

            payload = {
                "cmd": "display_modal_popup",
                "args": {
                    "request_id": request_id,
                    "popup_data": popup_data
                }
            }

            # Always enqueue payload so backend can deliver it when a GUI connects
            self.send_gui_update(payload)

            # Also try immediate in-process emit to reach already-connected clients
            try:
                import pytestflow.backend.event_bus as _eb
                if getattr(_eb.event_bus, "loop", None):
                    print("[RuntimeControl] Enqueued popup and sending immediate in-process event_bus emit")
                    asyncio.run_coroutine_threadsafe(
                        _eb.event_bus.emit("outbound", payload),
                        _eb.event_bus.loop
                    )
            except Exception as e:
                print("[RuntimeControl] immediate event_bus emit failed (will rely on queue). Error:", e)

            while self._pending_popups.get(request_id) is None and not self._shutdown:
                self._popup_condition.wait(timeout=0.2)

            if self._shutdown:
                self._pending_popups.pop(request_id, None)
                raise RuntimeError("Shutdown requested")

            return self._pending_popups.pop(request_id)

    def set_popup_response(self, request_id, button_pressed, response_text=None):
        with self._popup_condition:
            if request_id in self._pending_popups:
                self._pending_popups[request_id] = {
                    "button": button_pressed,
                    "text": response_text
                }
                self._popup_condition.notify_all()

    # GUI update queue API
    def send_gui_update(self, update_data: dict) -> None:
        """Called by steps/other threads to enqueue a GUI update payload."""
        self._gui_update_queue.put(update_data)

    def get_gui_update(self, timeout: float = 0.5):
        """Called by backend consumer (in executor) to dequeue a GUI update.

        Returns the update dict or None if timeout expires.
        """
        try:
            return self._gui_update_queue.get(timeout=timeout)
        except queue.Empty:
            return None


runtime_control = RuntimeControl()
