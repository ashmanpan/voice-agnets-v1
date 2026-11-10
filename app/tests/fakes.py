"""Fakes that keep tests fully offline.

`FakeLiveKitAPI` replaces `livekit.api.LiveKitAPI`: constructing it and
calling `.agent_dispatch.create_dispatch(request)` records the request in a
list instead of performing a network dispatch, and returns an object with an
`.id` like the real response.
"""
from types import SimpleNamespace


class _FakeAgentDispatch:
    def __init__(self, records):
        self._records = records

    async def create_dispatch(self, request):
        self._records.append(request)
        return SimpleNamespace(id="fake-dispatch-id")


class _FakeAPIInstance:
    def __init__(self, records):
        self.agent_dispatch = _FakeAgentDispatch(records)

    async def aclose(self):
        return None


class FakeLiveKitAPI:
    """Drop-in for `livekit.api.LiveKitAPI`.

    Instantiated with a shared `records` list; every constructed instance
    appends dispatched requests to it so a test can assert on them.
    """

    def __init__(self, records):
        self._records = records

    def __call__(self, *args, **kwargs):
        return _FakeAPIInstance(self._records)
