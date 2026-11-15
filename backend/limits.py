"""Bounded, memory-only protections for one local backend process."""
import hashlib
import os
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


class LimitError(Exception):
    def __init__(self, code, message, retry_after=60):
        self.code, self.message, self.retry_after = code, message, max(1, int(retry_after))
        super().__init__(message)


class RequestLimits:
    def __init__(self, daily=500, rpm=5, clock=time.time):
        self.daily, self.rpm, self.clock = daily, rpm, clock
        self.lock = threading.Lock()
        self.secret = os.urandom(32)
        self.clients = {}
        self.global_window = deque()
        self.active = set()
        self.day = ''
        self.used = 0
        self.provider_exhausted = False

    def _roll(self):
        now = datetime.fromtimestamp(self.clock(), ZoneInfo('America/Los_Angeles'))
        day = now.date().isoformat()
        if day != self.day:
            self.day, self.used, self.provider_exhausted = day, 0, False
        reset = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=now.tzinfo)
        return reset, max(1, int(reset.timestamp() - now.timestamp()))

    def _available(self):
        reset, wait = self._roll()
        if self.provider_exhausted:
            raise LimitError('provider_daily_limit', 'Google’s daily request quota has been reached. You can prepare a new search after the daily reset.', wait)
        if self.used >= self.daily:
            raise LimitError('daily_limit', f'Today’s {self.daily}-request budget has been used. Please return after the daily reset.', wait)
        return reset

    def client_key(self, host):
        return hashlib.blake2b(host.encode(), key=self.secret, digest_size=16).hexdigest()

    def guard(self, host, search=False, model=False):
        with self.lock:
            now = self.clock()
            # Expire client counters; no raw IPs, notes, or profiles are retained.
            self.clients = {k: v for k, v in self.clients.items() if v and v[-1] > now - 60}
            while self.global_window and self.global_window[0] <= now - 60:
                self.global_window.popleft()
            key = self.client_key(host)
            window = self.clients.setdefault(key, deque())
            while window and window[0] <= now - 60:
                window.popleft()
            if len(self.global_window) >= 30 or len(window) >= 15:
                raise LimitError('burst_limit', 'Too many requests. Please wait a minute before trying again.', 60)
            window.append(now)
            self.global_window.append(now)
            if search:
                if model:
                    self._available()
                if key in self.active:
                    raise LimitError('search_in_progress', 'A search is already running. Wait for it to finish or cancel it first.', 10)
                if len(self.active) >= 3:
                    raise LimitError('service_busy', 'The research service is busy. Please try again shortly.', 15)
                self.active.add(key)
            return key

    def release(self, key):
        with self.lock:
            self.active.discard(key)

    def reserve_gemini(self):
        with self.lock:
            self._available()
            now = self.clock()
            calls = getattr(self, 'model_calls', deque())
            while calls and calls[0] <= now - 60:
                calls.popleft()
            if len(calls) >= self.rpm:
                raise LimitError('model_rate_limit', 'Too many research requests. Please wait a minute before preparing another search.', 60)
            calls.append(now)
            self.model_calls = calls
            self.used += 1  # Reserve before the call; failures are counted conservatively.

    def exhaust_provider(self):
        with self.lock:
            _, wait = self._roll()
            self.provider_exhausted = True
            return wait

    def snapshot(self):
        with self.lock:
            reset, _ = self._roll()
            return {'dailyLimit': self.daily, 'remaining': max(0, self.daily - self.used), 'resetsAt': reset.astimezone(timezone.utc).isoformat(), 'providerExhausted': self.provider_exhausted}


limits = RequestLimits(daily=max(1, int(os.getenv('GEMINI_DAILY_LIMIT', '500'))), rpm=max(1, int(os.getenv('GEMINI_RPM_LIMIT', '5'))))
