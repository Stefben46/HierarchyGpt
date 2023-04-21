# HierarichyGpt

## Objective

making a multi purpose ai to create bigger projects to what Auto-gpt can do, with more efficiencies
Feel free to make suggestiong or to push Upgrades or fixes

- Has the ability to Create, Read, Write and Run files

## How does it work?
1. Makes a list of tasks to complete the specified objective
2. Executes the tasks that were made using other instances of GPT 3.5
3. Makes a list of taks to check if the objective was completed
4. the tasks are executed
5. Checks if the objective was completed succesfully based on the tasks results and expains it's response, if the objective was completed it stops itself
6. if the objective wasn't completed it makes another list of tasks to try to fix what is wrong
7. executes the list of tasks
8. checks another time and if the objective still isn't completed it continues with trying to fix the problem

### What are it's Pros?
- doesn't cost a lot since it doesn't use many tokens (obviously depending on the task that it needs to do)
- it's really focused on the objective and doesn't tend to stray away from it
- it's efficient
### what are it's Cons?
- it's actions are limited for now (can't run terminal commands or access the web)
- since it doesn't have an appropriate way of absorbing text efficiently it get's limited by the Token count with big amounts of text
- since it spins up a new instance of an AI for every time it writes a file, it can have problems of the different AIs not knowing exactly what the other one did (we are talking with 3 or more files but depends on the request)

## Example:

The objective is: create a python program that gives the current time as output
since it's a simple task it achieves it really easely and reliably
![image](https://user-images.githubusercontent.com/28029553/233624483-d468fab9-c3d2-4ca7-9bf0-db41d44168e7.png)

## How do i run it?
1. clone the repository
2. open the example.env file and put in your OpenAi key 
3. in the same file also decide and objective and write it in the OBJECTIVE line
4. save it and change it's name to just .env
5. run a Terminal instance in the same directory as the repository and write "python hgpt.py" to run it

### Credits:

BabyAgi: https://github.com/yoheinakajima/babyagi i started from their code, stripped it down completely and built it up like i wanted, to achieve my objective

AutoGpt: https://github.com/Significant-Gravitas/Auto-GPT i started with my porject because if wanted an autogpt with a different structure
