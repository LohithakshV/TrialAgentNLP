import os
import unittest
from unittest.mock import patch

import httpx

from backend.providers import _parse_json, gemini


class ProviderJson(unittest.TestCase):
    def test_parses_json_with_a_markdown_fence(self):
        self.assertEqual(_parse_json('```json\n{"ok": true}\n```'), {'ok': True})

    def test_parses_json_surrounded_by_text(self):
        self.assertEqual(_parse_json('prefix {"ok": 1} suffix'), {'ok': 1})

    def test_unparseable_json_still_raises(self):
        with self.assertRaises(ValueError):
            _parse_json('not json')


class ProviderGemini(unittest.IsolatedAsyncioTestCase):
    async def call(self, payload):
        def handler(request):
            return httpx.Response(200, json=payload)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-test-key'}):
                with patch('backend.providers.limits.reserve_gemini'):
                    return await gemini(client, 'instruction', {'query': 'test'}, {'type': 'object'})

    async def test_parses_a_text_response(self):
        result = await self.call({
            'candidates': [{'content': {'parts': [{'text': '{"score": 82}'}]}}],
        })
        self.assertEqual(result, {'score': 82})

    async def test_empty_candidates_are_an_error(self):
        with self.assertRaises(ValueError):
            await self.call({'candidates': [], 'promptFeedback': {'blockReason': 'SAFETY'}})

    async def test_empty_text_is_an_error(self):
        with self.assertRaises(ValueError):
            await self.call({'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': []}}]})
