import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from unittest.mock import patch

import httpx
from backend.limits import RequestLimits, LimitError
from backend.providers import gemini


class Limits(unittest.TestCase):
    def test_daily_reservation_is_atomic_and_hard_capped(self):
        limiter = RequestLimits(daily=500, rpm=1000)
        def attempt(_):
            try:
                limiter.reserve_gemini()
                return 1
            except LimitError:
                return 0
        with ThreadPoolExecutor(max_workers=12) as pool:
            self.assertEqual(sum(pool.map(attempt, range(550))), 500)
        self.assertEqual(limiter.snapshot()['remaining'], 0)

    def test_reset_uses_pacific_midnight(self):
        clock = [datetime(2026, 11, 14, 7, 59, tzinfo=timezone.utc).timestamp()]
        limiter = RequestLimits(daily=1, clock=lambda: clock[0])
        limiter.reserve_gemini()
        with self.assertRaises(LimitError):
            limiter.reserve_gemini()
        clock[0] += 120
        limiter.reserve_gemini()
        self.assertEqual(limiter.used, 1)

    def test_burst_duplicate_and_concurrency_limits(self):
        limiter = RequestLimits(max_concurrent=3)
        key = limiter.guard('client-a', search=True)
        with self.assertRaises(LimitError) as caught:
            limiter.guard('client-a', search=True)
        self.assertEqual(caught.exception.code, 'search_in_progress')
        limiter.guard('client-b', search=True)
        limiter.guard('client-c', search=True)
        with self.assertRaises(LimitError) as caught:
            limiter.guard('client-d', search=True)
        self.assertEqual(caught.exception.code, 'service_busy')
        limiter.release(key)
        limiter.guard('client-d', search=True)
        for i in range(30):
            try:
                limiter.guard('client-x')
            except LimitError:
                break
        else:
            self.fail('Burst requests were not limited')
        self.assertNotIn('client-a', limiter.clients)

    def test_model_rpm_blocks_before_daily_budget_is_spent(self):
        limiter = RequestLimits(rpm=1)
        limiter.reserve_gemini()
        with self.assertRaises(LimitError) as caught:
            limiter.reserve_gemini()
        self.assertEqual(caught.exception.code, 'model_rate_limit')
        self.assertEqual(limiter.used, 1)


class ProviderQuota(unittest.IsolatedAsyncioTestCase):
    async def test_google_daily_quota_is_distinct_from_temporary_throttle(self):
        for quota, code in [('GenerateRequestsPerDayPerProjectPerModel-FreeTier', 'provider_daily_limit'), ('GenerateRequestsPerMinute', 'provider_rate_limit')]:
            limiter = RequestLimits()
            def handler(request):
                return httpx.Response(429, json={'error': {'details': [{'quotaId': quota}]}})
            with patch('backend.providers.limits', limiter), patch.dict('os.environ', {'GEMINI_API_KEY': 'fake-key'}):
                async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                    with self.assertRaises(LimitError) as caught:
                        await gemini(client, 'instruction', {}, {'type': 'object'})
            self.assertEqual(caught.exception.code, code)
