from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
from models import State
from solver import Solver, evaluate
from retrieval import retrieve_examples

def build_graph(draft_solver, solver):
    builder = StateGraph(State)

    builder.add_node("draft", draft_solver)
    builder.add_edge(START, "draft")
    builder.add_node("retrieve", retrieve_examples)
    builder.add_node("solve", solver)
    builder.add_node("evaluate", evaluate)
    builder.add_edge("draft", "retrieve")
    builder.add_edge("retrieve", "solve")
    builder.add_edge("solve", "evaluate")

    def control_edge(state: State):
        if state.get("status") == "success":
            return END
        return "solve"

    builder.add_conditional_edges("evaluate", control_edge, {END: END, "solve": "solve"})
    checkpointer = MemorySaver()

    graph = builder.compile(
        checkpointer=checkpointer,
        # This tells the graph to break any time it goes to the "human" node
        interrupt_after=["evaluate"],
    )
    
    return graph