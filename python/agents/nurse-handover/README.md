# Nurse Handover Agent

## A. Overview & Functionalities

This project uses Google Cloud's Gemini generative AI model to create concise and informative nurse handover summaries from detailed medical records. It streamlines the handover process, reducing the risk of miscommunication and improving patient safety.

### Agent Details Table

| Feature              | Description                                                                                                                                                                                                                                                                           |
| :------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Interaction Type** | Conversational                                                                                                                                                                                                                                                                        |
| **Complexity**       | Intermediate                                                                                                                                                                                                                                                                          |
| **Agent Type**       | Single Agent (with sub-routines for summarization)                                                                                                                                                                                                                                    |
| **Vertical**         | Healthcare                                                                                                                                                                                                                                                                            |
| **Key Features**     | **Tools**: `list_available_shifts`, `list_patients`, `generate_shift_endorsement`.<br>**Data Management**: Reads patient medical records from local files.<br>**LLM processing**: Uses separate section models and summary models to segment and format the report into ISBAR format. |

### Example Interaction

Here is a 3-turn sample conversation showing how the agent works:

**User:** Hi!

**Assistant:** Hello! I'm your nurse shift handover assistant. My purpose is to help streamline your shift handover process by automatically generating comprehensive reports. I can generate a shift endorsement for patient **MHID123456789** for the shift that started on **2024-06-07T07:30:00** and ended on **2024-06-07T19:30:00**. Would you like me to go ahead and generate the report for you?

**User:** Yes, please!

**Assistant:** I have stored the following artifacts:
(1) raw patient input file at `MHID123456789-1717763400-1717806600-raw-inputs.txt`
(2) the endorsement report at `MHID123456789-1717763400-1717806600-endorsement.md`.

## B. Architecture Visuals

### Architecture Diagram

![Architecture Diagram](agent_pattern.png)

The system consists of the following key flow:

1. **List Patients:** List current patients of the identified nurse.
2. **List Shifts:** List shifts available for endorsement generation.
3. **Summary Generator:** Orchestrates the process. Retrieves the relevant medical record, filters irrelevant information, interacts with the Gemini API, and formats the summary into a markdown file.

## C. Setup & Execution

### Prerequisites & Installation

- **Google Credentials:** You need a GCP project _or_ Gemini API key for local testing. You need a GCP project for deployment to Cloud Run.
- **UV:** Ensure that you have [`uv`](https://docs.astral.sh/uv/getting-started/installation/) installed.

1. **Install dependencies in a virtual environment:**

```bash
uv sync --dev
```

2. **Set up Environment Variables:** Create a file named `.env` and update values as needed. You can refer to `.env.example` as a reference.

```bash
# If using API key: ML Dev backend config.
GOOGLE_API_KEY=YOUR_VALUE_HERE
GOOGLE_GENAI_USE_VERTEXAI=false

# If using Vertex on GCP: Vertex backend config
GOOGLE_CLOUD_PROJECT=YOUR_VALUE_HERE
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=true

AGENT_MODEL_NAME=gemini-2.5-flash
SECTION_MODEL_NAME=gemini-2.5-pro
SUMMARY_MODEL_NAME=gemini-2.5-flash
```

3. **Authenticate with GCP and enable VertexAI (if using GCP):**

```bash
gcloud auth login --update-adc
gcloud config set project PROJECT_ID
gcloud services enable aiplatform.googleapis.com
```

### Running the Agent

You can start the agent locally through either the CLI or UI:

- **Run the agent(s) API server (CLI):** `make api-server`
- **Run the agent with the ADK Web UI:** `make web`
- **Run the agent with the ADK CLI:** `make cli`

## D. Customization & Extension

- **Modifying the Flow:** You can alter the core logic, prompts, and initial state by modifying the `load_agent` function and callback hooks in `agents/nurse_handover/agent.py`. The ISBAR formatting templates are stored in `configs/` which can be tweaked for different summarization structures.
- **Adding Tools:** Plug in new tools or external APIs by defining new functions in `agents/nurse_handover/tools.py` and adding them to the `tools` array when initializing the `LlmAgent` in `agent.py`.
- **Changing Data Sources:** By default, patient records are loaded from the local `data/` directory (`PATIENT_FILE_DIR` in `tools.py`). To point to different databases or RAG components, update the `list_patients`, `list_available_shifts`, and `generate_shift_endorsement` functions in `tools.py` to fetch data from your preferred backend.

## E. Evaluation

While the core ADK might decouple evaluation directly from runtime, providing measurable validation of the AI's output is critical in healthcare.
_Note: Any custom evaluation scripts should be placed in the `/eval/` folder._

**Methodology & Scripts:**
To evaluate the agent, you can run the integration and unit tests using the command:

```bash
make test
```

The typical methodology involves:

1. **End-to-end testing:** Simulating the 3-turn interaction to ensure the agent correctly identifies shifts and patients, ultimately invoking the generator.
2. **Metrics:** Ensuring the final `.txt` and `.md` artifacts are successfully created and accurately incorporate the expected clinical formatting (ISBAR template) without omissions.
3. **Execution Scripts:** Code within `tests/` executes predefined user inputs and asserts that the `summary_report` output and the callback states transition as expected. The `/eval/` scripts would run further rigorous factual consistency checks on the LLM outputs.

## F. Deploy

Deployment guidelines should follow standard Agent Garden and Agent Engine procedures, which have been tested and verified for this project configuration.

### Agent Starter Pack Deployment

You can use the [Agent Starter Pack](https://goo.gle/agent-starter-pack) to create a production-ready version with automated CI/CD deployment scripts (Cloud Run, etc).

```bash
# Install the starter pack
uvx agent-starter-pack create my-nurse-handover -a adk@nurse-handover
```
