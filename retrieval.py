from langchain_community.retrievers import BM25Retriever
from langchain_core.runnables import RunnableConfig
from models import State
from utils import format_example, get_dataset_standard
import datasets

# Load dataset
ds = get_dataset_standard()

def retrieve_examples(state: State, config: RunnableConfig):
    top_k = config["configurable"].get("k") or 2
    ai_message = state["candidate"]
    id = config["configurable"].get("thread_id")

    test_ds = [row for row in ds if row["cp_id"] != id]
    retriever = BM25Retriever.from_texts([format_example(row) for row in test_ds])
    
    if not ai_message.tool_calls:
        # We err here. To make more robust, you could loop back
        raise ValueError("Draft agent did not produce a valid code block")
    code = ai_message.tool_calls[0]["args"]["code"]
    examples_str = "\n".join(
        [doc.page_content for doc in retriever.invoke(code)[:top_k]]
    )
    examples_str = f"""
You previously solved the following problems in this competition:
<Examples>
{examples_str}
<Examples>
Approach this new question with similar sophistication."""
    return {"examples": examples_str} 