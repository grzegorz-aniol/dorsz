from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field

# Import the function_tool decorator from the agents SDK to expose functions as tools
from agents import function_tool


class TopicItem(BaseModel):
    """
    Single topic entry tracked by the agent during a conversation.

    Fields:
        description (str): Short, concise description of a topic to investigate.
        asked (bool): Flag indicating whether the agent has already asked the user about this topic.
        conclusion (Optional[str]): Final conclusion/answer for this topic once resolved, or None if unresolved.
    """
    description: str = Field(
        ...,
        description="Short, concise description of a topic to investigate."
    )
    asked: bool = Field(
        False,
        description="Whether the agent already asked about this topic."
    )
    conclusion: Optional[str] = Field(
        None,
        description="Final conclusion/answer when resolved, otherwise None."
    )

    @property
    def answered(self) -> bool:
        """Computed convenience flag: True if the topic has a non-empty conclusion."""
        return bool(self.conclusion)


class TopicList:
    """
    Global singleton list of topics.

    This container is a singleton: all tool calls operate on the same shared instance,
    enabling the agent to coordinate a queue of topics to ask about and mark as answered.

    Internal structure:
        - items: List[TopicItem] where index starting at 0 identifies each topic.
    """
    _instance: Optional["TopicList"] = None

    def __new__(cls) -> "TopicList":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.items: List[TopicItem] = []
        return cls._instance

    # Core operations used by tool wrappers

    def add(self, description: str) -> int:
        item = TopicItem(description=description, asked=False, conclusion=None)
        self.items.append(item)
        return len(self.items) - 1

    def mark_answered(self, index: int, conclusion: str) -> bool:
        if index < 0 or index >= len(self.items):
            return False
        self.items[index].conclusion = conclusion
        # If something is concluded, it was implicitly "asked"
        self.items[index].asked = True
        return True

    def next_unanswered_index(self) -> Optional[int]:
        for i, it in enumerate(self.items):
            if not it.answered:
                return i
        return None

    def summary_lines(self) -> List[str]:
        lines: List[str] = []
        for i, it in enumerate(self.items):
            status = "ANSWERED" if it.answered else "OPEN"
            asked = "asked" if it.asked else "not-asked"
            conclusion = f" | conclusion: {it.conclusion}" if it.answered else ""
            lines.append(f"[{i}] {status} ({asked}) :: {it.description}{conclusion}")
        return lines


# Global singleton instance used by all tool functions
_GLOBAL_TOPICS = TopicList()


@function_tool
def add_topic(description: str) -> int:
    """
    Add a new topic to the global singleton list and return its index.

    Purpose:
        Use this tool to register a new, concise topic that the agent intends to
        investigate via conversation. The added topic is initially marked as:
            - asked = False
            - conclusion = None
        Topics are identified by their zero-based index in the global list.

    Args for LLM/Agent:
        description (str): A short description of the topic (1-2 sentences max).
                           Keep it specific and actionable to guide subsequent questions.

    Returns:
        int: The zero-based index of the newly added topic in the global list.

    Typical usage by the Agent:
        - When the user mentions a new issue/area worth exploring, call add_topic("...").
        - Store the returned index if you plan to refer to this item later (e.g., to mark it answered).
    """
    return _GLOBAL_TOPICS.add(description=description)


@function_tool
def mark_topic_answered(index: int, conclusion: str) -> bool:
    """
    Mark an existing topic as answered by providing its final conclusion.

    Purpose:
        Use this tool after you have gathered sufficient information from the user
        and you can state a clear conclusion or answer for the given topic.

    Args for LLM/Agent:
        index (int): Zero-based index of the topic to mark as answered.
        conclusion (str): The final conclusion/answer. Keep it concise but explicit.

    Returns:
        bool: True if the operation was successful (index valid), False otherwise.

    Notes:
        - This operation also sets asked=True implicitly, since conclusions follow investigation.
        - If the index is invalid (out of range), the tool returns False.
    """
    return _GLOBAL_TOPICS.mark_answered(index=index, conclusion=conclusion)


@function_tool
def next_unanswered_topic() -> int:
    """
    Find the next topic that is not yet answered and return its index, or -1 if none.

    Purpose:
        Use this tool to pick the next pending topic that lacks a conclusion.
        You may then ask the user targeted questions about it and eventually mark it answered.

    Args for LLM/Agent:
        (no arguments)

    Returns:
        int: The zero-based index of the next topic without a conclusion.
             Returns -1 if all topics are answered or the list is empty.

    Recommended flow:
        - idx = next_unanswered_topic()
        - if idx != -1:
            * Retrieve its description via get_topics_summary (or remember it from when added)
            * Ask the human specific questions (e.g., via ask_human) to resolve it
            * mark_topic_answered(idx, "...final conclusion...")
        - else:
            * All topics resolved. Proceed to final summary/report.
    """
    idx = _GLOBAL_TOPICS.next_unanswered_index()
    return -1 if idx is None else idx


@function_tool
def get_topics_summary() -> str:
    """
    Get a human-readable summary of all topics with their indices and status.

    Purpose:
        Use this tool to review the full set of topics and their current states
        (OPEN vs ANSWERED, asked/not-asked). This is helpful when deciding next steps
        or before producing a final report.

    Args for LLM/Agent:
        (no arguments)

    Returns:
        str: Multiline summary where each line has the format:
             [index] STATUS (asked|not-asked) :: description[ | conclusion: ... ]

    Example output:
        [0] OPEN (not-asked) :: Database connection times out randomly
        [1] ANSWERED (asked) :: Deploy pipeline fails on prod | conclusion: Missing secret ABC
    """
    lines = _GLOBAL_TOPICS.summary_lines()
    if not lines:
        return "No topics registered yet."
    return "\n".join(lines)
