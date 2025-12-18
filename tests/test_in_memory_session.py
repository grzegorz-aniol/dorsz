import asyncio

from agents.items import TResponseInputItem

from local_agents.in_memory_session import InMemorySession


async def _add_dummy_items(session: InMemorySession, count: int) -> None:
    for i in range(count):
        item: TResponseInputItem = {
            "role": "user",
            "content": f"message-{i}",
        }
        await session.add_items([item])


def test_in_memory_session_keeps_only_last_n_items():
    session = InMemorySession(session_id="test", max_items=4)

    async def _run() -> None:
        await _add_dummy_items(session, 10)
        items = await session.get_items()

        # Should keep only last 4
        assert len(items) == 4
        assert [it["content"] for it in items] == [
            "message-6",
            "message-7",
            "message-8",
            "message-9",
        ]

    asyncio.run(_run())


def test_in_memory_session_pop_and_clear():
    session = InMemorySession(session_id="test-pop", max_items=3)

    async def _run() -> None:
        await _add_dummy_items(session, 3)
        last = await session.pop_item()
        assert last is not None
        assert last["content"] == "message-2"

        await session.clear_session()
        items = await session.get_items()
        assert items == []

    asyncio.run(_run())
