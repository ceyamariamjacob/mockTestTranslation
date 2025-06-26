# English-to-Mocha Test LangGraph flow

This project aims to translate raw English sentences to Mocha Puppeteer tests, Using LangGraph flow, with Human-in-the-loop and reflection features.

A sample user login (username : "user" , password: "pass") and form page is used @ index.html

## Setup
Clone this repo:
```
git clone https://github.com/ceyamariamjacob/mockTestTranslation.git

cd mockTestTranslation
```

Install ollama:
```
brew install ollama
ollama pull llama3.2:latest
```

Setup python environment:
```
python3 -m venv venv
source venv/bin/activate
```

Install python dependencies:
```
pip install -r requirements.txt
pip install -U "langgraph-cli[inmem]"
```

Setup node environment:
```
npm install
```

Create .env file, and fill in required langsmith api key:
```
cp .env.example .env
```

Start langgraph server:
```
langgraph dev
```

In case of any puppeteer browser installation error:
```
npx puppeteer browsers install chrome
```

## Running the graph
1. After `langgraph dev`, enter `exit` when prompted to enter instruction. The langsmith studio should open up in browser after this.

2. Input an english instruction into 'Input' field in langsmith studio, and click submit. This starts the run , generates mocha code, and will ask for human input (accept/edit/ignore) in the terminal.

3. When prompted for an answer, enter your response to the code generated. errors/warnings encountered while compiling the code will be printed on the terminal for your reference.

4. accept: adds the input and response to few_shot_examples, and ends the run

   ignore: ends the run

   edit: prompts for human feedback on the code generated, and reflects on its code and human feedback, and generates new code, which will be then presented for human review, until the run is accepted/ignored.

5. Start next run by entering new input and submitting in langsmith studio interface

## Manually check if a testfile compiles successfully
```
npx mocha test/<testfile>
```
## TODO
->AgentInbox integration (interrupt usage)
->test validation logic to be reviewed


## 6/10 Setup for reflection + hitl node 
start running the graph:
```
langgraph dev
```

click submit on the graph in langsmith studio, and start the run to generate reflection and output, for the trace (which I have hardcoded for now)

While in interrupted state (Human node), head over to [AgentInbox](https://dev.agentinbox.ai/), and add a new inbox with following details:
1. Graph ID: `agent`
2. Deployment URL: `http://127.0.0.1:2024`
3. Name: (any name of your choice)

Here, you can handle the interrupt (Accept/ Edit: edit the response manually/ Ignore)

On accepting, the output generated will be written back into `intent.json` file's `demo` field, and the initial trace will be recorded in `traces` field as well.

*(6/11) Update:*

- [x] Edit functionality fixed: The generated output can be edited by the user, and on clicking `Accept`, the edited output is written into 'intent.json'.
- [x] Response functionality added: User can give a feedback to the output generated, and on clicking `Respond`, the output gets regenerated, and can be reviewed (accept/edit/respond/ignore) by the user further.


## Dockerized reflections + agent inbox (setup)
The Agent Inbox image is pushed as `docker-master.cdaas.oraclecloud.com/docker-cxsales-dev/agent-inbox:0.0.1`

To run the reflections graph along with it, build the `langgraph-project` image using:
```
docker build -t langgraph-project .
```

In a new terminal, start the ollama server:
```
ollama serve
```

Run the services:
```
docker compose up
```

To run the reflection graph with the trace as the input, run below commands in a new terminal:
```
source venv/bin/activate
python3 apicall.py
```

The Agent Inbox UI should be running at [localhost:3000](http://localhost:3000), where the interrupt from the graph's new thread wuuld be ready to be handled.
While in interrupted state (Human node), add a new inbox in Agent Inbox UI with following details:
1. Graph ID: `agent`
2. Deployment URL: `http://127.0.0.1:2024`
3. Name: (any name of your choice)

Only on accepting, the output generated will be written back into `intent.json` file's `traces` field.