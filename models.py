from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

class TestCase(TypedDict):
    inputs: str
    outputs: str

class State(TypedDict):
    # Candidate for retrieval + formatted fetched examples as "memory"
    candidate: AIMessage
    examples: str
    messages: Annotated[list[AnyMessage], add_messages]
    test_cases: list[TestCase]
    runtime_limit: int
    status: str

class writePython(BaseModel):
    """Write python code that resolves the problem."""

    reasoning: str = Field(..., description="Conceptual solution.")
    pseudocode: str = Field(..., description="Detailed English pseudocode.")
    code: str = Field(..., description="Valid Python 3 solution to the problem") 