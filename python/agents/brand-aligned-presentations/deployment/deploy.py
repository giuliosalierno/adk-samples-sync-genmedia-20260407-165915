# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
import os
import sys
import tomllib

import vertexai
from dotenv import load_dotenv, set_key
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from presentation_agent.agent import root_agent

# Force override from .env
load_dotenv(override=True)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
STAGING_BUCKET = os.getenv("GCP_STAGING_BUCKET")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")


ENV_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "", ".env")
)

vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    staging_bucket=STAGING_BUCKET,
)


# Function to update the .env file
def update_env_file(agent_engine_id, env_file_path):
    """Updates the .env file with the agent engine ID."""
    try:
        set_key(env_file_path, "AGENT_ENGINE_ID", agent_engine_id)
        print(
            f"Updated AGENT_ENGINE_ID in {env_file_path} to {agent_engine_id}"
        )
    except Exception as e:
        print(f"Error updating .env file: {e}")


def load_requirements():
    """Loads requirements from pyproject.toml."""
    pyproject_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    )
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    return pyproject_data["project"]["dependencies"]


def main(mode):
    # Build env_vars dynamically, ensuring all values are strings
    env_vars = {
        "GCP_PROJECT": str(os.getenv("GOOGLE_CLOUD_PROJECT")),
        "GCP_LOCATION": str(
            os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"
        ),
        "GEMINI_MODEL_NAME": str(
            os.getenv("GEMINI_MODEL_NAME") or "gemini-2.5-flash"
        ),
        "IMAGE_GENERATION_MODEL": str(
            os.getenv("IMAGE_GENERATION_MODEL") or "imagen-3.0-generate-002"
        ),
        "GCP_STAGING_BUCKET": str(os.getenv("GCP_STAGING_BUCKET") or ""),
        "DEFAULT_TEMPLATE_URI": str(os.getenv("DEFAULT_TEMPLATE_URI") or ""),
        "ENABLE_RAG": str(os.getenv("ENABLE_RAG") or "false"),
        "ENABLE_DEEP_RESEARCH": str(
            os.getenv("ENABLE_DEEP_RESEARCH") or "false"
        ),
        "GOOGLE_GENAI_USE_VERTEXAI": str(
            os.getenv("GOOGLE_GENAI_USE_VERTEXAI") or "True"
        ),
    }

    # Only add optional variables if they actually contain a value
    if os.getenv("DATASTORE_ID"):
        env_vars["DATASTORE_ID"] = str(os.getenv("DATASTORE_ID"))
    if os.getenv("MODEL_ARMOR_TEMPLATE_ID"):
        env_vars["MODEL_ARMOR_TEMPLATE_ID"] = str(
            os.getenv("MODEL_ARMOR_TEMPLATE_ID")
        )

    if mode == "update":
        logger.info("updating app in agent engine...")
        if AGENT_ENGINE_ID is not None:
            app = AdkApp(
                agent=root_agent,
                enable_tracing=True,
            )
            engine = agent_engines.get(AGENT_ENGINE_ID)
            engine.update(
                agent_engine=app,
                display_name="presentation_agent",
                requirements=load_requirements(),
                extra_packages=[
                    "./presentation_agent",
                ],
                env_vars=env_vars,
            )
        else:
            logger.info("no exisiting agent engine app resource found in env")

    elif mode == "create":
        logger.info("creating app in agent engine...")

        app = AdkApp(
            agent=root_agent,
            enable_tracing=True,
        )

        remote_app = agent_engines.create(
            app,
            display_name="presentation_agent",
            requirements=load_requirements(),
            extra_packages=[
                "./presentation_agent",
            ],
            env_vars=env_vars,
        )

        logging.info(
            f"Deployed agent to Vertex AI Agent Engine successfully, resource name: {remote_app.resource_name}"
        )
        update_env_file(remote_app.resource_name, ENV_FILE_PATH)
    else:
        logger.info("invalid mode")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy or Update")
    parser.add_argument(
        "--mode",
        type=str,
        default="create",
        help="Select if the deplying for the first time or updating existing",
    )
    args = parser.parse_args()
    main(args.mode)
