import re
import requests
import zipfile
import os
import datasets
from config import usaco_url, zip_path, extract_path

def filter_python_code(output: str) -> str:
    """
    Filters the model's output to extract only the Python code contained within ```python and ``` delimiters.
    
    Parameters:
        output (str): The raw output from the model.

    Returns:
        str: Filtered output containing only the Python code.
    """
    # Locate code block between ```python and ```
    code_block = re.search(r"```python(.*?)```", output, re.DOTALL)
    
    # If code block is found, return the content; otherwise, return an empty string
    if code_block:
        return code_block.group(1).strip()
    else:
        return output

def format_example(row):
    question = row["description"]
    answer = row["solution"]
    return f"""<problem>
{question}
</problem>
<solution>
{answer}
</solution>"""

def _hide_test_cases(inputs):
    copied = inputs.copy()
    if "test_cases" in copied:
        copied["test_cases"] = [
            {
                "inputs": "..." if len(tc["inputs"]) > 200 else tc["inputs"],
                "outputs": "..." if len(tc["outputs"]) > 200 else tc["outputs"]
            }
            for tc in copied["test_cases"]
        ]
    else:
        copied["test_cases"] = "..."
    return copied

def get_problem_ds(problem):
    test_path = "/Users/stevenyu/programmingsolver/usaco_data/datasets/usaco_v3/tests/" + problem["cp_id"] + "/"
    test_cases = []
    for i in range(int(problem["num_tests"])):
        test_cases.append({"inputs":"", "outputs":""})
        inFN = test_path + "I." + str(i+1)
        outFN = test_path + "O." + str(i+1)
        with open(inFN, "r") as file:
            test_cases[i]["inputs"] = file.read()
        with open(outFN, "r") as file:
            test_cases[i]["outputs"] = file.read()
    return {
        "title": problem["cp_id"],
        "messages": [("user", problem["description"])],
        "test_cases": test_cases,
        "runtime_limit": problem["runtime_limit"],
        "status": "in_progress",
    } 

def get_problem():
    print("-"*35 + " Problem Description " + "-"*35)
    title = input("Please input the title of the problem: ")
    print("\n\n")
    description = input("Please input the problem text: \n")
    print("\n\n")
    description += "\nInput Format:\n"
    description += input("Please describe the input format: (e.g. 'The first line of input contains an integer N (1 <= N <= 100000)... \n")
    print("\n\n")
    description += "\nOutput Format:\n"
    description += input("Please describe the output format: (e.g. 'The output should consist of N lines... \n")
    print("\n\n")
    print("-"*35 + " Test Cases " + "-"*35)
    test_case_num = int(input("Please input the number of test cases: "))
    test_cases = []
    for i in range(test_case_num):
        print("Test Case " + str(i+1) + ":")
        test_cases.append({"inputs":"", "outputs":""})
        test_cases[i]["inputs"] = input("Please input the input text: \n")
        test_cases[i]["outputs"] = input("Please input the output text: \n")
    print("\n\n")
    runtime_limit = int(input("Please input the runtime limit (if none, input 100): "))
    return {
        "title": title,
        "messages": [("user", description)],
        "test_cases": test_cases,
        "runtime_limit": runtime_limit,
        "status": "in_progress",
    }

#load sample of usaco problems
def get_dataset_standard():
    if not os.path.exists(extract_path):
        response = requests.get(usaco_url)
        with open(zip_path, "wb") as file:
            file.write(response.content)
        
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        os.remove(zip_path)

    ds = datasets.load_from_disk(os.path.join(extract_path, "usaco_v3_sampled_with_tests"))
    return ds

#load all usaco problems (not available online)
'''def get_dataset_official():
    ds = datasets.load_from_disk("/Users/stevenyu/programmingsolver/usaco_data/datasets/usaco_v3")
    return ds'''