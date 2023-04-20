#!/usr/bin/env python3
import os
import subprocess
from collections import deque
from typing import Dict, List
import importlib
import webbrowser
import time
import re
import openai
import pinecone
from dotenv import load_dotenv
import os

# Load default environment variables (.env)
load_dotenv()

# Engine configuration

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
assert OPENAI_API_MODEL, "OPENAI_API_MODEL environment variable is missing from .env"

if "gpt-4" in OPENAI_API_MODEL.lower():
    print(
        "\033[91m\033[1m"
        + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
        + "\033[0m\033[0m"
    )



# Table config
YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert YOUR_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

# Goal configuation
OBJECTIVE = os.getenv("OBJECTIVE", "")

# Model configuration
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.0))


# Extensions support begin

def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


DOTENV_EXTENSIONS = os.getenv("DOTENV_EXTENSIONS", "").split(" ")

# Command line arguments extension
# Can override any of the above environment variables
ENABLE_COMMAND_LINE_ARGS = (
    os.getenv("ENABLE_COMMAND_LINE_ARGS", "false").lower() == "true"
)
if ENABLE_COMMAND_LINE_ARGS:
    if can_import("extensions.argparseext"):
        from extensions.argparseext import parse_arguments

        OBJECTIVE, INITIAL_TASK, OPENAI_API_MODEL, DOTENV_EXTENSIONS = parse_arguments()

# Load additional environment variables for enabled extensions
if DOTENV_EXTENSIONS:
    if can_import("extensions.dotenvext"):
        from extensions.dotenvext import load_dotenv_extensions

        load_dotenv_extensions(DOTENV_EXTENSIONS)


assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env"

if "gpt-4" in OPENAI_API_MODEL.lower():
    print(
        "\033[91m\033[1m"
        + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
        + "\033[0m\033[0m"
    )

# Print OBJECTIVE
print("\033[94m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
print(f"{OBJECTIVE}")



# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY

main_task_list = deque([])
check_task_list = deque([])
terminal_output = ""


def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")[
        "data"
    ][0]["embedding"]


def openai_call(
    prompt: str,
    model: str = OPENAI_API_MODEL,
    temperature: float = OPENAI_TEMPERATURE,
    max_tokens: int = 2000,
):
    while True:
        try:
            if model.startswith("llama"):
                # Spawn a subprocess to run llama.cpp
                cmd = ["llama/main", "-p", prompt]
                result = subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True)
                return result.stdout.strip()
            elif not model.startswith("gpt-"):
                # Use completion API
                response = openai.Completion.create(
                    engine=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                return response.choices[0].text.strip()
            else:
                # Use chat completion API
                messages = [{"role": "system", "content": prompt}]
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    n=1,
                    stop=None,
                )
                return response.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            print(
                "The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again."
            )
            time.sleep(10)  # Wait 10 seconds and try again
        else:
            break
        






def task_projectManager(
    objective: str
):
    global main_task_list
    prompt = f"""
You are an AI that must complete an objective, but you can only do it through one or more of these four actions:
-Write File: Writes and creates text to a specified file with a specific extension using the data loaded in memory if it's present, explain extensively what must be written
-Research: write a question and loads the answer in memory
-Read File: Reads the text contained a specified single file and loads it into Memory, the file must exist
-Run File: Executes a single file from the terminal, use only if necessary
Your objective is to: '''{objective}'''
Write a list where you specify the actions that you need to accomplish the objective,
you don't have to use all of the actions, you can use more than one per type
With each one of the actions that are necessary you must use this formatting:
#@ [action name]: [filename]  [explanation]
#@ [action name]: [filename]  [explanation]
"""
    response = openai_call(prompt)
    new_tasks = response.split("#@")
    

    for task in new_tasks:
        separated = task.split(".")
        if separated[0].isnumeric and task.strip()!="":
            #action_name = separated[1].split(":")[0][1:]
            main_task_list.append({"task_id": separated[0], "task_whole": task})
    

def Execute(task,task_list):
    action = task["task_whole"].split(":")[0]
    if "Write File" in action:
        write_file(task,task_list)
    elif "Read File" in action:
        read_file(task)
    elif "Run File" in action:
        run_file(task)

    elif "Research" in action:
        research(task,task_list)

    else:
        print("Error Task isn't in the task list: " + task["task_whole"])
        



def write_file(task,task_list):
    filename = task["task_whole"].split(":")[1].split(" ")[1]
    if "/" in filename:
        folder_name = filename.split("/")[0]
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
    file = open("./Workspace/"+filename, "w")
    if ".txt" in filename:
        file.write(ask_text(task["task_whole"].split(filename)[1]))
    else:
        file.write(ask_code(task["task_whole"].split(filename)[1]))
    file.close()
    print("-file Written: "+filename)
    return
    
def read_file(task):
    global read_memory
    filename = task["task_whole"].split(":")[1].split(" ")[1]
    if "." in filename:
        folder_name = "Workspace"
        file_path = os.path.join(os.getcwd(), folder_name, filename)

        if os.path.isfile(file_path):

            file = open("./Workspace/"+filename, "r")
            read_memory = read_memory + "this is what's written inside the "+filename+" file: "+ file.read()
            file.close()
            print("-file Read: "+filename)
        else:
            print(filename+ " does not exist")
            read_memory = read_memory +" "+filename+ " does not exist if the file is necessary, it's a problem and the objective is not reached"


def run_file(task):
    global terminal_output
    filename = task["task_whole"].split(":")[1].split(" ")[1]
    print("-Run: "+filename)
    if ".py" in filename:
        result = subprocess.run('python ' + "./Workspace/"+filename, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output = result.stdout.decode('utf-8')
        error = result.stderr.decode('utf-8')
        
        print(filename+" output: "+result.stdout.decode('utf-8'))
        
        terminal_output = terminal_output +" the output of "+filename+ " is: "+ output+". "
        if len(error) > 1:
            print("the python file gave an error: "+result.stderr.decode('utf-8'))
            terminal_output = terminal_output + " "+ filename+ " gave out the error: " +error 
    elif ".html" in filename:
        webbrowser.open_new_tab("./Workspace/" +filename)
    else:
        print("file extension not supported")
        
    
    return

def research(task,task_list):
    global read_memory
    read_memory = read_memory + "this is the answer to the task "+task["task_whole"]+" the answer is: "+ask_ai(task["task_whole"],task_list)
    return

def ask_code(question_text):
    global read_memory

    prompt = f"""
    you are an AI specialized in writing code, write all the code that is needed by the question of your file and comment the text, 
    the question is: '{question_text}'
    the data loaded in memory is: '{read_memory}'
    """
    response = openai_call(prompt)
    if "'''" in response:
        response = response.split("'''")[1]
    return response

def ask_text(question_text):
    global read_memory

    prompt = f"""
    you are an AI specialized in doing tasks, complete it in a complete way, if present the data loaded in memory is necessary for the task
    the task is: '{question_text}'
    the data loaded in memory is: '{read_memory}'
    """
    return openai_call(prompt)

def ask_ai(question_text,task_list):
    tasks = ""
    for task in task_list:
        tasks = tasks +"/n"+task["task_whole"]
    prompt = f"""
    you are an AI specialized in answering questions, answer them in a complete way but don't go too far, 
    the question is: '{question_text}'
    the context of the question is: '{tasks}'
    """
    return openai_call(prompt)

def check(task_list):
    global read_memory
    global terminal_output
    read_memory = ""
    terminal_output = ""
    
    
    global check_task_list
    tasks = ""
    for task in task_list:
        tasks = tasks +"/n"+task["task_whole"]
    prompt = f"""
    You are an AI that must check if the objective was completed successfully, but you can only do it through one or more of these four actions:
    -Research: Write a question and loads the answer in Memory
    -Read File: Reads contents of a specified single file and loads into Memory
    -Run File: Executes a single file from the terminal, loads the output in Memory
    the objective was to: '''{OBJECTIVE}'''
    the tasks that were executed to accomplish the objective are '''{tasks}'''
    the text loaded in memory will be checed by anothe AI
    Write a list where you specify the actions to check if the objective was achieved,
    you don't have to use all of the actions, you can use more than one per type
    With each one of the actions you need you must use this formatting:
    #@ [action name]: [filename]  [explanation]
    #@ [action name]: [filename]  [explanation]
    """

    print("\033[36m\033[1m" + "\n*****Tasks For Checking Objective Completition*****\n" + "\033[0m\033[0m")
    response = openai_call(prompt)
    new_tasks = response.split("#@")

    for task in new_tasks:
        separated = task.split(".")
        if separated[0].isnumeric and task.strip()!="":
            check_task_list.append({"task_id": separated[0], "task_whole": task})
    
    for task in check_task_list:
        print(task["task_whole"])
        
    print("\033[36m\033[1m" + "\n*****Executing Tasks*****\n" + "\033[0m\033[0m")
    for task in check_task_list:
        Execute(task,check_task_list)
    interpret()
        
def interpret():
    output = read_memory +" "+ terminal_output
    prompt = f""" 
    You are an AI tasked with deciding if an objective was completed completely successfully or not.
    you decide this based on an objective that has to be completed and a list of data, that shows what was accomplished
    the objective was: '''{OBJECTIVE}'''
    the list of data is '''{output}'''
    answer yes if the objective was completely achieved or no if it wasn't completely, do it with this formatting:
    #@ No: [reasoning]
    #@ Yes: [reasoning]
    """
    #print(output)
    response = openai_call(prompt)
    print("\033[33m\033[1m" + "\nWas The Objective Completed?" + response + "\033[0m\033[0m")
    
    if "#@ No" in response:
        fixer(response)
        
    
def fixer(reason):
    global check_task_list
    global read_memory
    global terminal_output
    check_task_list.clear()
    read_memory = ""
    terminal_output = ""
    prompt = f""" 
    You are an AI that must fix what is not working, but you can only do it through one or more of these four actions:
    -Write File: Writes and creates text to a specified file with a specific extension, explain extensively what must be written
    -Research: write a question and loads the answer in memory
    -Read File: Reads contents of a specified single file and load into Memory
    -Run File: Executes a single file from the terminal, use only if necessary
    you will receive a reason of why it isn't working as input and you will have to fix it so that you accomplish the objective
    the reason is: '''{reason}'''
    Your objective is to: '''{OBJECTIVE}'''
    Write a list where you specify the actions to fix the objective,
    you don't have to use all of the actions, you can use more than one per type
    With each one of the actions you need you must use this formatting:
    #@ [action name]: [filename]  [explanation]
    #@ [action name]: [filename]  [explanation]
    """
    
    print("\033[36m\033[1m" + "\n*****Fixing The problems Trough tasks*****\n" + "\033[0m\033[0m")
    response = openai_call(prompt)
    new_tasks = response.split("#@")

    for task in new_tasks:
        separated = task.split(".")
        if separated[0].isnumeric and task.strip()!="":
            check_task_list.append({"task_id": separated[0], "task_whole": task})
    
    for task in check_task_list:
        print(task["task_whole"])
    for task in check_task_list:
        Execute(task,check_task_list)
    check(check_task_list)

print("\033[36m\033[1m" + "\n*****Generating Tasks*****\n" + "\033[0m\033[0m")


# Add the first task
read_memory=""
task_projectManager(OBJECTIVE)
print("\033[33m\033[1m" + "\nGenerated Tasks:\n" + "\033[0m\033[0m")
for task in main_task_list:
    print(task["task_whole"])

print("\033[31m\033[1m" + "\n*****STARTED*****\n" + "\033[0m\033[0m")

for task in main_task_list:
    Execute(task,main_task_list)

check(main_task_list)


print("\033[31m\033[1m" + "\n*****SHUTDOWN*****\n" + "\033[0m\033[0m")
