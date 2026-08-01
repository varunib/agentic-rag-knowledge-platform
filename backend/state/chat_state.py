from typing import TypedDict, Optional, List


class ChatState(TypedDict):
    question: str
    session_id: str
    model: str

    route: Optional[str]

    context: str
    web_results: str

    answer: str

    citations: List

    confidence: float

    verification: str

    tool_result: str

    memory: list