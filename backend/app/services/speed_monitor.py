import time
from collections import deque


class SpeedMonitor:
    def __init__(self, window_seconds=5):
        self._window_seconds = window_seconds
        self._samples: deque[tuple[float, int]] = deque()
        self._current_total = 0
        self._start_time = None  # 延迟初始化，记录第一次采样时间

    def add_sample(self, size: int):
        now = time.monotonic()
        if self._start_time is None:
            self._start_time = now  # 只有在产生第一个流量时才开始计时

        self._samples.append((now, size))
        self._current_total += size
        self._clean_expired(now)

    def _clean_expired(self, now: float):
        while self._samples and (now - self._samples[0][0] > self._window_seconds):
            _, expired_size = self._samples.popleft()
            self._current_total -= expired_size

    @property
    def current_speed(self) -> float:
        """
        平均速度，单位：字节/秒
        """
        now = time.monotonic()
        if self._start_time is None:
            return 0.0

        self._clean_expired(now)

        # 计算逻辑优化：
        # 实际经历的时间 = 当前时间 - 第一次采样时间
        # 有效窗口时间 = min(实际经历的时间, 设定的窗口时间)
        elapsed = now - self._start_time

        # 避免 elapsed 为 0 导致 ZeroDivisionError（极短时间内的首次请求）
        actual_window = min(elapsed, self._window_seconds)

        if actual_window <= 0:
            return 0.0

        return self._current_total / actual_window
