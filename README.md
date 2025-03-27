# USACO Programming Problem Solver

This project uses AI models (Claude 3 Opus and GPT-4o) to solve competitive programming problems, particularly focusing on USACO-style problems. It features a retrieval-augmented system that finds similar problems with solutions to assist in solving new problems, and gives the user the option to use human-in-the-loop.

## Features

- Solves USACO-style competitive programming problems
- Uses retrieval-augmented generation with examples from past problems
- Supports both interactive and non-interactive solving modes (human in the loop)
- Provides detailed diagnostics on solving attempts
- Evaluates code against test cases

## Setup

### Prerequisites

- Python 3.8+
- API keys for Anthropic and OpenAI

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/usaco-solver.git
cd usaco-solver
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set your API keys as environment variables:
```bash
OPENAI_API_KEY='your-openai-api-key'
LANGCHAIN_API_KEY='your-langchain-api-key'
ANTHROPIC_API_KEY='your-anthropic-api-key'
```

## Usage

### Solving Your Own Problem

To solve your own programming problem, run:

```bash
python main.py
```

The program will prompt you for:
1. The problem description
2. Input format
3. Output format
4. Example inputs/outputs
5. Additional constraints (time/memory limits)

It will then attempt to solve the problem, showing its thought process and generating code.

### Interactive Mode

When running in interactive mode:
1. The solver will make an initial attempt
2. You'll see diagnostic information about the attempt
3. You can provide feedback to guide the solver
4. You can specify how many more attempts it should make
5. This cycle continues until the problem is solved or you exit

### Example Session

```bash
$ python main.py

----------------------------------- Problem Description -----------------------------------
Please input the title of the problem: Cow Crossing

Please input the problem text: 
Farmer John has N cows (1 ≤ N ≤ 100,000) that need to cross a river. Each cow has a weight w_i and a swimming speed s_i...

Please describe the input format:
The first line contains an integer N (1 ≤ N ≤ 100,000).
The next N lines each contain two integers: w_i and s_i...

Please describe the output format:
Output a single integer: the minimum total time needed for all cows to cross...

----------------------------------- Test Cases -----------------------------------
Please input the number of test cases: 2
Test Case 1:
Please input the input text: 
3
10 2
5 3
7 5
Please input the output text: 
11
Test Case 2:
Please input the input text: 
5
10 2
5 5
7 3
2 1
4 4
Please input the output text: 
13

Please input the runtime limit (if none, input 100): 5

[Solver attempts solution]

************************************** Previous Attempt Diagnostic **************************************

Thought Process:
I need to find the minimum total time... This is a well-known problem that can be solved using the "ratio rule"...
[Abbreviated reasoning]

Code:
def min_crossing_time(cows):
    # Calculate crossing time for each cow
    crossing_times = [(w/s, w, s) for w, s in cows]
    # Sort by crossing time
    crossing_times.sort()
    # [... calculation logic ...]
    return int(total_time)
# [... rest of solution ...]

Test Case Results:
Test Case 1: wrong answer. Expected '11', got '17.0'

Please type your feedback for the agent below 
(e.g. what algorithms to use, error explanations, etc.)
> Your approach is incorrect. This isn't about cumulative time. Each cow crosses independently...

How many times do you want the solver to run without additional feedback? 
If you want to terminate this solve process, enter 0.
> 1

[Solver makes another attempt with your feedback]

************************************** Previous Attempt Diagnostic **************************************

Thought Process:
I see my mistake. Let me reconsider... This is a scheduling problem.
The key insight: if we sort cows by increasing w_i/s_i, we minimize the waiting time...
[Abbreviated reasoning]

Code:
def min_crossing_time(cows):
    # Sort cows by w/s ratio
    cows.sort(key=lambda x: x[0]/x[1])
    # [... corrected calculation logic ...]
    return int(total_time)
# [... rest of solution ...]

Test Case Results:
Test Case 1: passed

Code successful.
```

### Non-Interactive Mode

To run the solver in non-interactive mode (useful for batch testing):

```python
from main import solve_no_interrupt, initialize_solvers, build_graph
from utils import get_problem
from langsmith import Client

draft_solver, solver = initialize_solvers()
graph = build_graph(draft_solver, solver)
client = Client()

problem = get_problem()  # Get problem definition
solve_no_interrupt(3, problem, graph, client)  # Try 3 times
```

### Changing Models

You can modify which AI models are used in the `initialize_solvers` function in `main.py`:

```python
def initialize_solvers():
    prompt = hub.pull("wfh/usaco-draft-solver")
    llm_claude = ChatAnthropic(model="claude-3-opus-20240229", max_tokens=4096, temperature=0.2)
    llm_openai = ChatOpenAI(model="gpt-4o", temperature=0.0) 

    draft_solver = Solver(llm_claude, prompt.partial(examples=""))
    solver = Solver(llm_claude, prompt)  # Change to llm_openai to use GPT-4o
    
    return draft_solver, solver
```

## Project Structure

- `main.py` - Entry point and high-level control functions
- `models.py` - Data models and state definitions
- `execution.py` - Code execution and testing logic
- `retrieval.py` - Example retrieval functionality
- `solver.py` - Problem-solving components
- `graph.py` - Workflow graph definition
- `utils.py` - Utility functions
- `config.py` - Configuration settings
- `download_dataset.py` - Dataset downloading utility

## Troubleshooting

### API Key Issues

If you get authentication errors:
1. Double-check your API keys and set them directly through the environment
2. Ensure you have sufficient credits/quota on your API accounts (Claude limits will sometimes be too low)

### Model Performance

For best results:
1. Provide detailed problem descriptions with clear input/output specifications
2. Include multiple test cases
3. When giving feedback, be specific about algorithms or errors

## Acknowledgments

- This project uses the USACO dataset for retrieval-based problem solving
- Powered by Anthropic's Claude and OpenAI's GPT models
- Built with LangChain and LangGraph frameworks 
- Based on paper ["Can Language Models Solve Olympiad Programming?"](https://arxiv.org/pdf/2404.10952v1)