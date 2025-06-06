from langgraph.graph import StateGraph, START
from typing import Optional, TypedDict, Dict, Any, Literal
from langchain_ollama import ChatOllama
import subprocess, os
from langgraph.types import Command, interrupt
from langgraph.graph import END
from typing import TypedDict
import pathlib
from datetime import datetime
import uuid
from dotenv import load_dotenv
load_dotenv()

class GraphState(TypedDict):
    input: str
    messages: list
    output: str
    valid: bool
    explanation: str
    human_input: Optional[str]
    human_review: Optional[str]
    thread_id: Optional[str]
    action: str

class GeneratedReason(TypedDict):
    code: str
    explanation: str

class ReflectionState(TypedDict):
    reflection: str

class HumanInterruptConfig(TypedDict):
    allow_ignore: bool
    allow_respond: bool
    allow_edit: bool
    allow_accept: bool

#for agent inbox
class ActionRequest(TypedDict):
    action: str
    args: dict

class HumanInterrupt(TypedDict):
    action_request: ActionRequest
    config: HumanInterruptConfig
    description: Optional[str]


class HumanResponse(TypedDict):
    type: Literal['accept', 'ignore', 'response', 'edit']
    response: Optional[str]

few_shot_examples = [
  {
    "instruction": "Open the homepage and check if the title contains 'Welcome'",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Homepage Title', () => {\n  it('should contain Welcome in the title', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    const title = await page.title();\n    if (!title.includes('Welcome')) throw new Error('Title does not contain Welcome');\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Ensure the username field is visible on the login section",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Login Field Visibility', () => {\n  it('should show the username field', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    const visible = await page.$eval('#username', el => !!el);\n    if (!visible) throw new Error('Username field not visible');\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Submit the contact form with dummy data",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Contact Form Submission', () => {\n  it('should submit the form', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    await page.type('#fullname', 'Test User');\n    await page.type('#email', 'test@example.com');\n    await page.type('#message', 'Hello from test');\n    await page.click('button');\n    await page.waitForTimeout(1000);\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Check that the login button is disabled until both fields are filled",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Login Button Behavior', () => {\n  it('should enable button only after input fields are filled', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    let isDisabled = await page.$eval('button', el => el.disabled);\n    if (!isDisabled) throw new Error('Button should be disabled initially');\n    await page.type('#username', 'user');\n    await page.type('#password', 'pass');\n    isDisabled = await page.$eval('button', el => el.disabled);\n    if (isDisabled) throw new Error('Button should be enabled after input');\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Check if error alert appears on wrong credentials",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Login Error Alert', () => {\n  it('should show alert on invalid login', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    page.on('dialog', async dialog => await dialog.dismiss());\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    await page.type('#username', 'wrong');\n    await page.type('#password', 'wrong');\n    await page.click('button');\n    await page.waitForTimeout(1000);\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Ensure the message field has a max length attribute",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Message Field Maxlength', () => {\n  it('should have maxlength attribute', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    const maxLength = await page.$eval('#message', el => el.getAttribute('maxlength'));\n    if (!maxLength) throw new Error('No maxlength attribute');\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Ensure the form resets after submission",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Form Reset Behavior', () => {\n  it('should clear fields after form submit', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    await page.type('#fullname', 'Reset User');\n    await page.type('#email', 'reset@example.com');\n    await page.type('#message', 'Reset this form');\n    await page.click('button');\n    await page.waitForTimeout(2000);\n    const name = await page.$eval('#fullname', el => el.value);\n    if (name !== '') throw new Error('Form did not reset');\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Verify the background is a gradient",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Background Gradient', () => {\n  it('should use a gradient background', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundImage);\n    if (!bg.includes('gradient')) throw new Error('No gradient background');\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Check if form submission shows a success message",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Success Message Display', () => {\n  it('should display success after form submit', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    await page.type('#fullname', 'Success User');\n    await page.type('#email', 'success@example.com');\n    await page.type('#message', 'Checking success');\n    await page.click('button');\n    await page.waitForSelector('#successMsg');\n    const msg = await page.$eval('#successMsg', el => el.textContent || '');\n    if (!msg.includes('successfully')) throw new Error('Success message not shown');\n    await browser.close();\n  });\n});"
  },
  {
    "instruction": "Verify password input is type=password",
    "test": "import puppeteer from 'puppeteer';\nimport path from 'path';\nimport { fileURLToPath } from 'url';\n\nconst __filename = fileURLToPath(import.meta.url);\nconst __dirname = path.dirname(__filename);\n\ndescribe('Password Field Type', () => {\n  it('should be of type password', async () => {\n    const browser = await puppeteer.launch({\n      headless: false,\n      executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',\n    });\n    const page = await browser.newPage();\n    await page.goto('file://' + path.join(__dirname, '../index.html'));\n    const type = await page.$eval('#password', el => el.type);\n    if (type !== 'password') throw new Error('Password input is not type=password');\n    await browser.close();\n  });\n});"
  }
]

all_reflections=['']
llm=ChatOllama(model="llama3.2:latest", temperature=0.2)

#for agent inbox
def _generate_test_markdown(state: GraphState) -> str:
    """Generate markdown description of the test for human review."""
    return f"""
    ## Test Code Review

    *Instruction*: {state['input']}

    *Generated Test Code*:
    ```typescript
    {state['output']}
    Explanation: {state.get('explanation', 'No explanation provided')}

    Validation Status: {'✅ Valid' if state.get('valid', False) else '❌ Invalid'}
    """


def generate_test_code(state: GraphState)->GraphState:
    
    example_strs = [
        f"Instruction: {ex['instruction']}\nCode:\n{ex['test']}\n"
        for ex in few_shot_examples
    ]
    examples_text = "\n\n".join(example_strs)

    reflections=[
        f"Human Instruction: {reflection}\n" for reflection in all_reflections
    ]
    reflection_text="\n\n".join(reflections)

    prompt = f"""
    You are an expert in writing Mocha tests using Puppeteer (no chai) in TypeScript.

    Given a simple English instruction, generate a valid Mocha test in TypeScript using Puppeteer.

    Guidelines:
    - import correct modules and libraries
    - Use `async` functions.
    - Include appropriate `before` or `beforeEach` hooks for browser/page setup.
    - Close browser if necessary.
    - Only output code — no explanations.
    - Use CSS selectors when referring to UI elements.

    Here are some examples:

    {examples_text}

    Here are some reflections you had generated in the past to be very careful of:

    {reflection_text}

    Now for this new instruction:
    Instruction: {state["input"]}
    Code:
    """


    llm_here=llm.with_structured_output(GeneratedReason)
    response=llm_here.invoke([{"role": "user", "content": prompt}])
    print(response)
    return {**state, "output":response["code"],"explanation":response["explanation"]}


def validate_mocha_tests(state:GraphState)->GraphState:
    code=state["output"]
    cwdir=pathlib.Path(os.getcwd())

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    cwdir=(cwdir / "test")
    test_file=os.path.join(cwdir,f"test_{timestamp}.spec.ts")
    with open(test_file,"w") as f:
        f.write(code)
    # Compile with tsc 
    compile_proc1 = subprocess.run(
        ["npx", "tsc", "--noEmit",test_file],
        cwd=cwdir,
        capture_output=True,
        text=True,
    )

    if compile_proc1.returncode != 0:
        print("\n❌ TypeScript Compilation Error:")
        print("STDOUT:\n", compile_proc1.stdout)
        print("STDERR:\n", compile_proc1.stderr)
        return {**state, "valid": False}

        
    return {**state, "valid":True}

def should_interrupt(state:GraphState)->bool:
    return state.get("valid") is False

# for AGENT INBOX (changes required) 
# def hitloop(state: GraphState):
#     request: HumanInterrupt = {
#         "config": {
#             "allow_ignore": True,
#             "allow_respond": False,
#             "allow_edit": True,
#             "allow_accept": True
#         },
#         "description": _generate_test_markdown(state) # Generate a detailed markdown description.
#     }
#     print("\n\n---HITL NODE----\n\n")
#     response: HumanResponse=interrupt(request)[0]

#     if response['type']=="ignore":
#         print("\n----IGNORING----\n")
#         # return {**state,"human_input":None}
#         return Command(goto='final')
#     elif response['type']=="accept":
#         print("\n----ACCEPTING----\n")
#         new_example={"instruction":state["input"],
#                      "test":state["output"]}
#         few_shot_examples.append(new_example)
#         # return {**state,"valid":True,"human_input":None}
#         return Command(goto="final")
#     elif response['type']=="edit":
#         print("\n----EDITING----\n")
#         feedback=response['response']
#         all_reflections.append(feedback)
#         return Command(goto="reflection")
#     return state


def hitloop(state: GraphState)->GraphState:  
    print("----HITL NODE----")
    print("The following Instruction was given:")
    print(state["input"])
    print("\n\nThe following code was generated:")
    print(state["output"])
    print("\n\n So far, this is the reflection generated:\n")
    print(all_reflections[-1])

    while True:  
        action=input("Do you want to accept, edit, or ignore?: ")
        if action=="accept":
            new_example={"instruction":state["input"],
                        "test":state["output"]}
            few_shot_examples.append(new_example)
            state["human_input"]=None
            print("\n----CODE ACCEPTED----\n")
            return state
        elif action=="ignore":
            print("\n----CODE IGNORED----\n")
            state["human_input"]=None
            return state
        elif action=="edit":
            print("\n----CODE NEEDS CHANGES----\n")
            humanresponse=input("What changes do you expect?: ")
            state["human_input"]=humanresponse
            return state
        else:
            continue


def router2(state:GraphState)->str:
    if state.get('human_input'):
        return 'reflect'
    else:
        return 'end'

def reflection(state: GraphState)->GraphState:
    prompt=f"""
    You are an advanced AI assistant qa engineer who is tasked with generating a detailed reflection 
    on your previous action of code generation which was incorrect, while translating raw english instructions to moach typescript tests.

    Heres the input that was given to you initially:
    <input>
    {state['input']}
    </input>

    Heres the incorrect code that you had generated:
    <code>
    {state['output']}
    </code>

    Heres the explanation you had created:
    <explanation>
    {state['explanation']}
    </explanation>

    Heres the human response and feedback to your code that was not compiling properly:
    <human>
    {state['human_input']}
    </human>

    Your new task is to do the following:
    1. Carefully examine your original (incorrect) code.
    2. Carefully examine the human response that is the corrected explanation to be focused on.
    3. Think deeply about why your code was wrong.
    4. Generate clear, concise thinking into exactly where your thought process went wrong, and how you can avoid making the same mistake in the future.
    5. Read the 'reflection-generation-rules' below for more details.

    <reflection-generation-rules>
    1. Reflections must be concise, and direct.
    2. Reflections should never be duplicated. If the reflection you want to generate already exists in the 'all-reflections' section, do not generate it again.
    3. Avoid generating multiple, similar reflections, as this will bloat the list, and can lead to confusion.
    4. Reflections should be specific and actionable, focusing on improving the explanation generation process based on the reasoning.
    5. Reflections should be focused on the root cause of the error in explanation and code generation.
    6. Reflections should be written in the present tense, as they will be used to guide future decision-making.

    </reflection-generation-rules>

    With all of this in mind, please generate a summary of new reflections on your mistake to assist with future decision-making. You do not need to be overly verbose, the less the better. Your main goal is to figure out exactly what went wrong, and how you can avoid making the same mistake in the future.
    Think long and hard, go!

    """
    llm_here=llm.with_structured_output(ReflectionState)
    response = llm_here.invoke([{"role":"system","content":prompt}])
    print(response)
    all_reflections.append(response.get('reflection'))
    return {**state}



def format_output(state: GraphState) -> Dict[str, Any]:
    return {
        "instruction": state["input"],
        "typescript_test_code": state["output"],
        "valid": state["valid"],
        "reason": state.get("explanation",""),
        "thread_id":state.get("thread_id","")
    }

def build_graph():
    builder = StateGraph(GraphState)
    builder.add_node("generate", generate_test_code)
    builder.add_node("validate", validate_mocha_tests)
    builder.add_node("final", format_output)
    builder.add_node("hitloop",hitloop)
    builder.add_node("reflection",reflection)

    builder.add_edge(START,"generate")
    builder.add_edge("generate", "validate")
    builder.add_conditional_edges("validate",should_interrupt,{True:'hitloop',False:'final'})
    builder.add_conditional_edges('hitloop',router2,{
        "reflect":"reflection",
        "end":"final"
    })
    builder.add_edge('reflection','generate')
    return builder.compile()

# Run the graph
graph = build_graph()
while(True):

    instruction = input("Enter an instruction: ")
    if(instruction=="exit"):
        break

    config={"configurable":{"thread_id":uuid.uuid4()}}
    
    result = graph.invoke({"input": instruction},config=config)
    
    print("\nInstruction:", result["input"])
    print("Reason:", result.get("reason", "N/A"))
    print("Code Compiles? :", result["valid"])
    print("\n-------- Generated Test Code --------")
    print(result["output"])
