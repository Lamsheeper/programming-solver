from langchain import hub
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from solver import Solver
from graph import build_graph
import os
from langsmith import Client
from utils import _hide_test_cases, get_problem_ds, get_problem
import re
from langchain_core.tracers.context import tracing_v2_enabled
from utils import filter_python_code
from retrieval import ds

def initialize_solvers():
    prompt = hub.pull("wfh/usaco-draft-solver")
    llm_claude = ChatAnthropic(model="claude-3-opus-20240229", max_tokens=4096, temperature=0.2)
    llm_openai = ChatOpenAI(model="gpt-4o", temperature=0.0) 

    draft_solver = Solver(llm_claude, prompt.partial(examples=""))
    solver = Solver(llm_claude, prompt)
    
    return draft_solver, solver

def solve(problem, graph, client):

    # First iteration of solver
    config = {"configurable": {"thread_id": problem["title"], "k": 2}}

    #Runs the solver num_trials times    
    def run_solver(stream_state, num_trials, new_config):
        with tracing_v2_enabled(client=client):
            for _ in range(num_trials):
                events = graph.stream(stream_state, new_config)
                for event in events:
                    for value in event.values():
                        if type(value) == tuple:
                            continue
                        messages = value.get("messages")
                        if messages:
                            if isinstance(messages, list):
                                messages = value["messages"][-1]
                            print(
                                "Assistant:",
                                str(messages.content).replace("\n", "\\n")[:50],
                            )
                        elif value.get("examples"):
                            print("Retrieved examples:\n\n", value["examples"][:100] + "...")
                        elif value.get("candidate"):
                            print(str(value["candidate"].content)[:200])
                if graph.get_state(config).values["status"] == "success":
                    print("Code successful.")
                    display_diagnostic()
                    break
                print("Continuing...")

    # Displays diagnostic for most recent attempt
    def display_diagnostic():
        most_recent_state = list(graph.get_state_history(config))[0]
        snapshot = graph.get_state(most_recent_state.config)
        
        # Find the most recent AI message
        ai_message = None
        for message in reversed(snapshot.values["messages"]):
            if hasattr(message, '__class__') and message.__class__.__name__ == 'AIMessage':
                ai_message = message
                break
        
        print("*" * 35 + " Previous Attempt Diagnostic " + "*" * 35)
        print("\n\nThought Process:\n\n")
        
        if ai_message and hasattr(ai_message, 'content') and ai_message.content:
            print(ai_message.content)
        else:
            print("No AI message content found.")
        
        print("\n\nCode:\n\n")
        
        code = "N/A"
        if ai_message and hasattr(ai_message, 'tool_calls') and ai_message.tool_calls:
            try:
                code = ai_message.tool_calls[0]["args"]["code"]
            except (IndexError, KeyError):
                code = "Tool call exists but code not found"
        elif ai_message and ai_message.content:
            # Try to extract code from content if no tool calls
            code = filter_python_code(ai_message.content)
        
        print(code)
        print("\n\nTest Case Results:\n\n")
        
        # Get the most recent Tool message which should contain test results
        test_results = "No test results found"
        for message in reversed(snapshot.values["messages"]):
            if hasattr(message, '__class__') and message.__class__.__name__ == 'ToolMessage':
                test_results = message.content
                break
        
        # Format and limit test results
        if test_results != "No test results found":
            # Extract pass rate if available
            pass_rate_match = re.search(r"Pass rate: (\d+)/(\d+)", test_results)
            if pass_rate_match:
                print(f"Pass rate: {pass_rate_match.group(1)}/{pass_rate_match.group(2)}")
            
            # Extract test cases with limited output
            pattern = r"<test id=(\d+)>\n(.*?)\n</test>"
            matches = re.findall(pattern, test_results, re.DOTALL)
            
            if matches:
                for test_id, result in matches:
                    # Limit each test case result to 100 characters
                    if len(result) > 100:
                        result = result[:97] + "..."
                    print(f"Test Case {test_id}: {result}")
            else:
                # If we couldn't parse test cases, just limit the overall output
                if len(test_results) > 300:
                    test_results = test_results[:297] + "..."
                print(test_results)
        else:
            print(test_results)

    # Gets human-in-the-loop feedback from the user on the previous attempt
    def get_user_feedback():
        feedback = input('''Please type your feedback for the agent below 
                         (e.g. what algorithms to use, error explanations, etc.) \n''')
        return graph.update_state(
            config,
            values={
                "messages": [
                    (
                        "user",
                        feedback,
                    )
                ]
            },
        )
        
    run_solver(problem, 1, config) #first iteration of solver
    while True and graph.get_state(config).values["status"] != "success": #keeps solving and asking for feedback until either the program is successful or the user terminates
        display_diagnostic()
        updated_config = get_user_feedback()
        trials = input('''How many times do you want the solver to run without additional feedback? 
                       If you want to terminate this solve process, enter 0. \n''')
        if trials == 0:
            print("Process terminated.")
            break
        run_solver(None, int(trials), updated_config)

'''Solves a problem without human in the loop'''
def solve_no_interrupt(trials, problem, graph, client):
    '''Runs the solver 'trials' times without human feedback'''

    config = {"configurable": {"thread_id": problem["title"], "k": 2}}
    
    def concat_test_case(s: str):
        print(s[:133])

        pattern = r"<test id=\d+>(.*?)</test>"
        # Find all matches
        matches = re.findall(pattern, s, re.DOTALL)

        # Print a few characters from each test case
        for i, match in enumerate(matches, start=1):
            print(f"Test Case {i}:\n {match[:50]}...") 

    def display_diagnostic():
        most_recent_state = list(graph.get_state_history(config))[0]
        snapshot = graph.get_state(most_recent_state.config)
        ai_message = snapshot.values["messages"][-2]
        print("*" * 35 + " Previous Attempt Diagnostic " + "*" * 35)
        print("\n\nThought Process:\n\n")
        if ai_message.content:
            print(ai_message.content)
        print("\n\nCode:\n\n")
        if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
            print(ai_message.tool_calls[0]["args"]["code"])
        else:
            print(filter_python_code(ai_message.content))
        print("\n\nTest Case Results:\n\n")
        concat_test_case(snapshot.values["messages"][-1].content)

    #Runs the solver num_trials times
    def run_solver(stream_state, num_trials, new_config):
        with tracing_v2_enabled(client=client):
            for _ in range(num_trials):
                events = graph.stream(stream_state, new_config)
                for event in events:
                    for value in event.values():
                        if type(value) == tuple:
                            continue
                        messages = value.get("messages")
                        if messages:
                            if isinstance(messages, list):
                                messages = value["messages"][-1]
                            print(
                                "Assistant:",
                                str(messages.content).replace("\n", "\\n")[:50],
                            )
                        elif value.get("examples"):
                            print("Retrieved examples:\n\n", value["examples"][:300] + "...")
                        elif value.get("candidate"):
                            print(str(value["candidate"].content)[:200])
                most_recent_state = list(graph.get_state_history(config))[0]
                snapshot = graph.get_state(most_recent_state.config)
                print(snapshot.values["messages"][-1].content[:133])
                if graph.get_state(config).values["status"] == "success":
                    print("\n\n\n\n\n\nCode successful.\n\n\n\n\n\n")
                    display_diagnostic()
                    return ""

    run_solver(problem, 1, config) #first iteration
    if graph.get_state(config).values["status"] != "success":
        run_solver(None, trials-1, config) #other trials-1 iterations
        display_diagnostic()

    return graph.get_state(config).values["status"]

def main():
    draft_solver, solver = initialize_solvers()
    graph = build_graph(draft_solver, solver)
    
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "programming_solver"
    
    client = Client(hide_inputs=_hide_test_cases, hide_outputs=_hide_test_cases)

    #Sample code to test a problem with a solver from the dataset
    row = ds[0]
    print(row["description"])
    print(row["problem_level"])

    row_input = get_problem_ds(row)
    '''solve_no_interrupt(5, row_input, graph, client) #solves without human in the loop
    solve(row_input, graph, client)'''

    
    #Solves a problem inputted by the user
    #user_input = get_problem()
    solve(row_input, graph, client)

if __name__ == "__main__":
    main()