import re

from tools.topics_registry import TopicList, TopicItem


def test_topics_list_basic_flow():
    pl = TopicList()
    # Reset singleton state for test isolation
    pl.items = []

    # Initially empty
    assert pl.next_unanswered_index() is None
    assert pl.summary_lines() == []

    # Add two topics
    idx0 = pl.add("Database connection times out randomly")
    idx1 = pl.add("Deployment pipeline fails intermittently")

    assert idx0 == 0
    assert idx1 == 1
    assert len(pl.items) == 2

    # Next unanswered should be 0
    assert pl.next_unanswered_index() == 0

    # Mark first as answered
    ok = pl.mark_answered(idx0, "Root cause: connection pool exhaustion")
    assert ok
    assert pl.items[0].asked is True
    assert pl.items[0].answered is True
    assert pl.items[0].conclusion == "Root cause: connection pool exhaustion"

    # Next unanswered should now be 1
    assert pl.next_unanswered_index() == 1

    # Summary lines format
    lines = pl.summary_lines()
    assert len(lines) == 2
    # Check basic structure: [index] STATUS (asked|not-asked) :: description[ | conclusion: ... ]
    assert re.match(r"^\[0\] ANSWERED \(asked\) :: Database connection times out randomly \| conclusion: .+$", lines[0])
    assert lines[1] == "[1] OPEN (not-asked) :: Deployment pipeline fails intermittently"


def test_mark_answered_invalid_index():
    pl = TopicList()
    # Reset singleton state for test isolation
    pl.items = []

    pl.add("Some issue")
    assert len(pl.items) == 1

    # Invalid indices should return False
    assert pl.mark_answered(-1, "x") is False
    assert pl.mark_answered(1, "y") is False

    # Still one item and unanswered
    assert pl.next_unanswered_index() == 0
