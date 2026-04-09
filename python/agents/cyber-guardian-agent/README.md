# 🛡️ Cyber Guardian Agent

## A. Overview & Functionalities

### 📋 Agent Details

| Attribute | Description |
| :--- | :--- |
| **Interaction Type** | ⚙️ **Workflow** (Structured step-by-step execution with conditional routing) |
| **Complexity** | 🧠 **Advanced** (Multi-agent orchestration, conditional logic, tool piping) |
| **Agent Type** | 👥 **Multi-Agent System** (Hierarchical Orchestrator with 4 Specialized Sub-agents) |
| **Vertical** | 🔒 **Cybersecurity / Security Operations (SecOps)** |

---

### ✨ Key Features

The Cyber Guardian Agent leverages a **hierarchical multi-agent architecture** built on Google's Agent Development Kit (ADK) to automate incident triage, investigation, and response.

#### 🧠 1. Orchestration & Routing
*   **Orchestrator Agent**: Acts as the central brain. It parses raw alert data (e.g., EDR detections, Phishing emails, IOC matches) and manages the execution flow.
*   **Dynamic Paths**: It intelligently reroutes the investigation path based on evidence. For instance, it runs **Threat Intel** *before* **Investigation** for IOC alerts, but *after* **Investigation** for process-heavy EDR alerts to verify newly discovered indicators.

#### 🛠️ 2. Specialized Python Tools
*   **Native Python Integration**: All forensic and investigative tools are implemented as standard Python functions, integrated via ADK's `FunctionTool`. This ensures low latency and seamless data passing between agents.
*   **BigQuery Integration**: Tools are optimized to query high-capacity BigQuery tables for logs, asset inventory, and threat intelligence, effectively serving as a high-speed RAG (Retrieval-Augmented Generation) source for security context.

#### 👥 3. Specialized Sub-Agents
*   **Triage Agent**: Handles deduplication and context enrichment. It queries asset inventory to determine if the target is a high-criticality asset.
*   **Investigation Agent**: Digs deep into process and network logs to confirm the blast radius and derive new Indicators of Compromise (IOCs).
*   **Threat Intel Agent**: Performs batch lookups on file hashes, IPs, and domains against a threat intelligence knowledge base.
*   **Response Agent**: Maps findings to predefined playbooks and recommends surgical response actions.

#### 🤝 4. Human-In-The-Loop (HITL) Safety
*   **Guardrails**: Critical response actions (e.g., host isolation) are flagged to require explicit approval, ensuring that automation supports rather than replaces expert judgment.

---

## B. Architecture Visuals

![Cyber Guardian Architecture](agent_pattern.png)

---

## C. Setup & Execution

### 🛠️ Prerequisites & Installation

Follow these steps to set up the environment and prepare the agent for execution.

**1. Clone the Repository**
```bash
git clone <your-repo-url>
cd cyber_guardian
```

**2. Python Environment Setup**
Ensure you have **Python 3.10+** and **uv** installed.
```bash
# Install the package and dependencies
uv sync --dev
```

**3. Google Cloud Authentication**
The agent requires access to BigQuery. Authenticate your local environment:
```bash
gcloud auth application-default login
```

---

### 📄 Configuration (.env)

The agent uses environment variables for project-specific configurations. A `.env` file should be located at `cyber_guardian/.env`.

**Example `.env` configuration:**
```env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
GOOGLE_CLOUD_LOCATION="your-gcp-region"
BQ_DATASET="<your_bq_dataset>"
MODEL_ID="model_id"

```

> [!IMPORTANT]
> Ensure `GOOGLE_CLOUD_PROJECT` matches your actual GCP project ID where the BigQuery tables are hosted.

---

### 📊 Optional: Populate BigQuery Tables

If you are setting up the environment for the first time, you can populate the required BigQuery tables using the provided CSV files in the `sample_data/` directory.

> [!NOTE]
> The data in `sample_data/` is synthetically generated for demonstration purposes.


**1. Create the BigQuery Dataset**
```bash
# Ensure environment variables are set or replaced directly
bq --location=US mk --dataset ${GOOGLE_CLOUD_PROJECT}:${BQ_DATASET}
```

**2. Load Data from CSV Files**
```bash
bq load --autodetect --source_format=CSV ${BQ_DATASET}.asset_inventory ./sample_data/asset_inventory.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.endpoint_process_events ./sample_data/endpoint_process_events.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.incident_management ./sample_data/incident_management.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.network_connection_log ./sample_data/network_connection_log.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.response_playbooks ./sample_data/response_playbooks.csv
bq load --autodetect --source_format=CSV ${BQ_DATASET}.threat_intelligence_kb ./sample_data/threat_intelligence_kb.csv
```

---

### 🚀 Running the Agent

You can interact with the Cyber Guardian Agent through a web interface or directly via the command line.

#### Option 1: Web UI (Recommended)
Launch the ADK web interface to visualize the multi-agent workflow and tool calls.
```bash
adk web --port 8081
```
Open `http://localhost:8081` in your browser and select the `cyber_guardian_orchestrator` agent.

#### Option 2: CLI (Direct Execution)
Run the agent directly from the terminal for quick testing.
```bash
adk run cyber_guardian:root_agent --input "Raw alert text here..."
```

**Example Test Query:**
```bash
adk run cyber_guardian:root_agent --input "IOC_Match: hostname: kvm01, user: admin, ip_address: 192.168.1.50, IOC: high_risk_hash_123 ........."
```

#### 🧪 Using Sample Inputs for Testing

You can use the examples provided in `sample_input.txt` to test the agent via CLI or Web UI.

> [!NOTE]
> The inputs in `sample_input.txt` are synthetically generated for demonstration.

### Alternative: Using Agent Starter Pack

You can also use the [Agent Starter Pack](https://goo.gle/agent-starter-pack) to create a production-ready version of this agent with additional deployment options:

```bash
# Create and activate a virtual environment
python -m venv .venv && source .venv/bin/activate

# Install the starter pack and create your project
pip install --upgrade agent-starter-pack
agent-starter-pack create my-cyber-guardian -a local@.
```

<details>
<summary>⚡️ Alternative: Using uv</summary>

If you have [`uv`](https://github.com/astral-sh/uv) installed, you can create and set up your project with a single command:
```bash
uvx agent-starter-pack create my-cyber-guardian -a local@.
```
This command handles creating the project without needing to pre-install the package into a virtual environment.

</details>

---

## D. Customization & Extension

The Cyber Guardian Agent is designed to be extensible. Whether you want to add new investigation capabilities or change the underlying data sources, here is how you can hack on the project.

### 🧠 1. Modifying the Agent Flow & Logic

The intelligence and routing logic of the system are determined by the orchestrator.

*   **Tweak Prompts**: To change how agents behave or interpret alerts, edit the instructions in `cyber_guardian/prompt.py` (for the Orchestrator) or the `prompt.py` files within each sub-agent directory (e.g., `cyber_guardian/sub_agents/triage/prompt.py`).
*   **Alter Orchestration**: The root agent definition and its sub-agent list are located in `cyber_guardian/agent.py`. Adjust the `sub_agents` list or the agent's model selection here.
*   **Add New Intents**: If you want the agent to handle new types of alerts (e.g., "Network Anomaly"), update the "Step 1: Parse & Classify" section in `cyber_guardian/prompt.py`.

### 🛠️ 2. Adding New Tools & APIs

The agents interact with the world through Python function tools.

*   **Define Functions**: Create new Python functions in `cyber_guardian/tools.py`. These functions should return JSON-serializable strings for the agents to consume.
*   **Plug in External APIs**: You can easily integrate tools for Virustotal, CrowdStrike, or Jira by adding their SDK calls within a new tool function.
*   **Register Tools**: To make a tool available to an agent, import it into the relevant agent's file (e.g., `sub_agents/investigation/agent.py`) and add it to the `tools` list via `FunctionTool(your_new_tool)`.

### 📊 3. Changing Data Sources (RAG)

The agent currently treats BigQuery as its primary source of truth (RAG).

*   **Switch Datasets**: You can point the entire system to a different BigQuery dataset by updating the `BQ_DATASET` variable in your `.env` file.
*   **Modify Database Queries**: If your schema differs from the default, update the SQL queries within the tool functions in `cyber_guardian/tools.py`.
*   **Use Different Backends**: While optimized for BigQuery, you can swap the database logic in `tools.py` to query Elasticsearch, Splunk, or local JSON/CSV files by changing the internally called Python libraries.

---

## E. Evaluation

Ensuring the reliability and accuracy of the Cyber Guardian Agent is critical before deploying it in a live SecOps environment. While the Agent Development Kit (ADK) focuses on agent orchestration, we implement a custom evaluation framework located in the `/eval/` directory.

### 🧪 Evaluation Methodology

Our evaluation methodology treats the multi-agent system as a complete pipeline, measuring its performance against a curated dataset of historical alerts ("ground truth" dataset). We evaluate both the intermediate steps (sub-agent performance) and the final outcome (orchestrator synthesis).

**The process involves:**
1.  **Dataset Ingestion**: Feeding a test suite of raw alerts (Phishing, EDR triggers, IOC matches, and benign anomalies) into the system.
2.  **Execution Logging**: Tracing the agent's routing decisions, tool calls, and payload arguments.
3.  **Assertion Checking**: Comparing the agent's generated response plan and derived IOCs against manually verified analyst playbooks.

### 📈 Key Metrics

When running evaluations, we care about the following metrics:
*   **Routing Accuracy**: Did the Orchestrator choose the correct sub-agent path (e.g., calling Threat Intel *before* Investigation for an IOC alert)?
*   **Entity Extraction Recall**: Did the agents successfully extract all relevant entities (IPs, hashes, hostnames) from the raw text to pass into the Python tools?
*   **False Positive Rate (FPR)**: How often did the system recommend a disruptive action (e.g., host isolation) for a benign or duplicate alert?
*   **Tool Execution Success Target**: What percentage of BigQuery tool invocations resulted in valid SQL execution vs. malformed queries or API errors?

---

## F. Deploy

### 🚀 Agent Garden & Starter Pack Integration

The Cyber Guardian Agent is designed for seamless onboarding to the **Google Cloud Agent Garden** ecosystem. It utilizes the **Agent Starter Pack** to generate automated deployment scripts, allowing the agent to be deployed quickly across various Google Cloud compute environments (such as **Cloud Run, App Engine, and GKE**).

This approach eliminates the need for manual Dockerfile maintenance or custom environment-specific deployment scripts in your repository.

> [!IMPORTANT]
> **Deployment Scope**: The first phase of Agent Garden onboarding is intended for **self-contained agents**. The agent should leverage existing workspace triggers and external data surfaces (like existing BigQuery datasets) rather than full infrastructure deployment orchestrations.

---

### 🛠️ Prerequisites

To prepare the agent for deployment via the Agent Starter Pack:
-   **Python 3.10+**
-   **`uv` Package Manager** (Required for lock file generation)
-   **Gemini CLI** (For automated adaptation)

---

### 🤖 Automated Adaptation with Gemini CLI

The integration process uses the **Gemini CLI** to adapt your workspace structure and inject required Starter Pack templates.

1.  **Open Gemini CLI** in your workspace.
2.  **Submit the following prompt template** to adapt the codebase:

```text
Your task is to adapt this ADK agent for integration with the Agent Starter Pack.

1. Modify pyproject.toml:
   - Convert all dependencies to the uv standard using [project] and [project.optional-dependencies].
   - Add the [tool.agent-starter-pack] metadata section.
   - Add 'agent-starter-pack' as a dev dependency.

2. Update Agent Source Code:
   - Add the flexible authentication block to the main agent Python file.

3. Update Documentation:
   - In README.md, replace existing setup instructions with `uv sync --dev` and add the "Alternative: Using Agent Starter Pack" section.

4. Generate Lock File:
   - Execute `uv lock` to generate the `uv.lock` file.
```

---

### 🧪 Local Verification

Before releasing the agent for Agent Garden onboarding, verify the lockfile and package compiling step locally.

**1. Create a workspace package:**
```bash
uvx agent-starter-pack create cyber-guardian-deploy -a local@. --auto-approve -o target
```

**2. Install and Test:**
```bash
cd target/cyber-guardian-deploy
make install
make test
```

> [!TIP]
> **Code Quality Workflow**: Successfully integrating with the Starter Pack automatically provides a non-blocking code quality reporting trigger. You can run the linter local checks with:
> ```bash
> make lint
> ```

---

### 📦 Production Rollout

After successfully building the `uv` locking layer and packaging verification, your agent is bundle-ready. The Agent Garden Console consumes the injected template mapping configurations inside `pyproject.toml` to provision the agent in the customer tenant project safely and effectively.


