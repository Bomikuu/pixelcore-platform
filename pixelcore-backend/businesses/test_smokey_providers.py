from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from smokey_assistant.providers import get_provider
from smokey_assistant.contracts import AssistantError


class SmokeyProviderTests(SimpleTestCase):
    def test_provider_destinations_and_formats(self):
        envelopes = {
            "openai": {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": '{"summary":"Done","highlights":[]}',
                            }
                        ],
                    }
                ]
            },
            "anthropic": {
                "content": [
                    {"type": "text", "text": '{"summary":"Done","highlights":[]}'}
                ]
            },
            "gemini": {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": '{"summary":"Done","highlights":[]}'}]
                        }
                    }
                ]
            },
            "openrouter": {
                "choices": [
                    {"message": {"content": '{"summary":"Done","highlights":[]}'}}
                ]
            },
        }
        for name, payload in envelopes.items():
            with (
                self.subTest(name=name),
                patch("smokey_assistant.providers.base.requests.request") as send,
            ):
                send.return_value = Mock(
                    status_code=200, json=Mock(return_value=payload)
                )
                result = get_provider(name).summarize(
                    "test-key", "test-model", {"metrics": {}}, 1024
                )
                self.assertEqual(result.narrative["summary"], "Done")
                self.assertIsNone(result.input_tokens)
                self.assertTrue(send.call_args.args[1].startswith("https://"))
                self.assertFalse(send.call_args.kwargs["allow_redirects"])

    def test_errors_do_not_include_provider_response_or_key(self):
        with patch(
            "smokey_assistant.providers.base.requests.request",
            return_value=Mock(status_code=401),
        ):
            with self.assertRaises(AssistantError) as caught:
                get_provider("openai").summarize("private-secret", "model", {}, 100)
            self.assertNotIn("private-secret", str(caught.exception))
            self.assertEqual(caught.exception.code, "INVALID_CREDENTIAL")

    def test_unknown_provider_is_rejected(self):
        for provider in ("https://arbitrary.example", [], {}, None):
            with self.assertRaises(AssistantError):
                get_provider(provider)

    def test_invalid_summary_preserves_reported_token_usage(self):
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": '{"summary":"","highlights":[]}',
                        }
                    ],
                }
            ],
            "usage": {"input_tokens": 30, "output_tokens": 10},
        }
        with patch(
            "smokey_assistant.providers.base.requests.request",
            return_value=Mock(status_code=200, json=Mock(return_value=payload)),
        ):
            with self.assertRaises(AssistantError) as caught:
                get_provider("openai").summarize("test-key", "test-model", {}, 100)
            self.assertEqual(caught.exception.provider_result.input_tokens, 30)
            self.assertEqual(caught.exception.provider_result.output_tokens, 10)
