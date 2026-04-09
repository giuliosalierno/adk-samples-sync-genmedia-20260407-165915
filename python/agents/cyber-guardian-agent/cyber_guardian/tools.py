import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any

from google.cloud import bigquery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Helper Function to convert BigQuery rows to JSON ---
def bq_rows_to_json(rows: list[Any]) -> str:
    """
    Converts a list of BigQuery Row objects to a JSON string,
    handling datetime objects by converting them to ISO 8601 strings.
    """

    def datetime_converter(o: Any) -> str:
        """Custom converter for json.dumps to handle non-serializable types."""
        if isinstance(o, datetime):
            # Convert datetime objects to their ISO 8601 string representation
            return o.isoformat()
        # Raise the default TypeError for all other unsupported types
        raise TypeError(
            f"Object of type {o.__class__.__name__} is not JSON serializable"
        )

    # Convert the list of Row objects to a list of dictionaries
    list_of_dicts = [dict(row) for row in rows]

    # Use the custom datetime_converter function in json.dumps
    return json.dumps(list_of_dicts, default=datetime_converter)


# --- Triage Tool ---
def triageQueryTool(hostname: str, alert_type: str) -> str:
    """
    Checks for duplicate incidents and enriches a host with business context.
    - Arg hostname: The hostname from the alert (e.g., 'kvm010019506d1b').
    - Arg alert_type: The type of the alert (e.g., 'IOC_MATCH').
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset = os.getenv("BQ_DATASET")
    client = bigquery.Client(project=project_id)

    # 1. Deduplication Check (Now uses AlertType instead of PrimaryIOC)
    dedup_query = f"""
        SELECT IncidentID, CreationTimestamp FROM `{project_id}.{dataset}.incident_management`
        WHERE PrimaryHost = @hostname AND AlertType = @alert_type
        AND CreationTimestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("hostname", "STRING", hostname),
            bigquery.ScalarQueryParameter(
                "alert_type", "STRING", alert_type
            ),  # Updated parameter
        ]
    )
    duplicate_rows = list(client.query(dedup_query, job_config=job_config).result())

    if duplicate_rows:
        return json.dumps(
            {"is_duplicate": True, "existing_incident": duplicate_rows[0]["IncidentID"]}
        )

    # 2. Context Enrichment (This part remains the same)
    context_query = f"SELECT Owner, BusinessCriticality FROM `{project_id}.{dataset}.asset_inventory` WHERE Hostname = @hostname"
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("hostname", "STRING", hostname)]
    )
    asset_rows = list(client.query(context_query, job_config=job_config).result())

    return json.dumps(
        {
            "is_duplicate": False,
            "asset_context": dict(asset_rows[0])
            if asset_rows
            else "No asset context found.",
        }
    )


# --- Investigation Tool ---
def investigationQueryTool(
    alert_type: str,
    hostname: str,
    parent_process: str | None = None,
    destination_ip: str | None = None,
) -> str:
    """
    Performs a detailed investigation based on the alert type.
    - Arg alert_type: The type of alert ('EDR_DETECTION', 'IOC_MATCH', 'PHISHING_EMAIL').
    - Arg hostname: The hostname to investigate.
    - Arg parent_process: (Optional) The parent process for EDR alerts.
    - Arg destination_ip: (Optional) The malicious IP for IOC_MATCH alerts.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset = os.getenv("BQ_DATASET")
    client = bigquery.Client(project=project_id)

    if alert_type == "EDR_DETECTION" and parent_process:
        query = f"""
            SELECT EventTimestamp, ProcessName, CommandLine FROM `{project_id}.{dataset}.endpoint_process_events`
            WHERE Hostname = @hostname AND ParentProcessName = @parent_process
            ORDER BY EventTimestamp DESC LIMIT 10
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("hostname", "STRING", hostname),
                bigquery.ScalarQueryParameter(
                    "parent_process", "STRING", parent_process
                ),
            ]
        )
        rows = list(client.query(query, job_config=job_config).result())
        return bq_rows_to_json(rows)

    if alert_type == "IOC_MATCH" and destination_ip:
        query = f"""
            SELECT log_timestamp, source_ip, destination_ip, destination_port FROM `{project_id}.{dataset}.network_connection_log`
            WHERE source_host = @hostname AND destination_ip = @destination_ip
            ORDER BY log_timestamp DESC LIMIT 10
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("hostname", "STRING", hostname),
                bigquery.ScalarQueryParameter(
                    "destination_ip", "STRING", destination_ip
                ),
            ]
        )
        rows = list(client.query(query, job_config=job_config).result())
        return bq_rows_to_json(rows)

    return "Query did not match a known investigation type. Please provide more specific parameters."


# --- Threat Intel Tool ---
def threatIntelQueryTool(indicators: list) -> str:
    """Enriches indicators of compromise using the threat_intelligence_kb table."""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset = os.getenv("BQ_DATASET")
    client = bigquery.Client(project=project_id)

    # Assumes indicators is a list of strings, e.g., ["392a...", "d8e8fca..."]
    query = f"""
        SELECT IOC_Value, IsMalicious, ThreatName, Confidence FROM `{project_id}.{dataset}.threat_intelligence_kb`
        WHERE IOC_Value IN UNNEST(@indicators)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("indicators", "STRING", indicators)
        ]
    )
    rows = list(client.query(query, job_config=job_config).result())

    if not rows:
        return json.dumps({"error": f"No threat intel found for IOCs: {indicators}"})

    return bq_rows_to_json(rows)


# --- Response Tools ---
def getPlaybookTool(triggering_condition: str) -> str:
    """
    Retrieves the appropriate response playbook based on a trigger.
    - Arg triggering_condition: The condition to match, e.g., "ThreatName = 'Cobalt Strike C2'".
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset = os.getenv("BQ_DATASET")
    client = bigquery.Client(project=project_id)

    query = f"""
        SELECT ActionCommand, RequiresApproval FROM `{project_id}.{dataset}.response_playbooks`
        WHERE TriggeringCondition = @trigger
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("trigger", "STRING", triggering_condition)
        ]
    )
    rows = list(client.query(query, job_config=job_config).result())
    return bq_rows_to_json(rows)


def responseExecutionTool(action: str, target: str) -> str:
    """Simulates executing a response action such as IP block or host isolation."""
    # In a real system, this would trigger a SOAR playbook or call an API.
    logger.info(f"Executing response action '{action}' on target '{target}'.")
    return json.dumps({"status": "success", "action": action, "target": target})


def createIncidentTool(alert_type: str, hostname: str, user: str, severity: str) -> str:
    """
    Creates a new incident record in the incident_management table.
    - Arg alert_type: The type of the alert (e.g., 'EDR_DETECTION').
    - Arg hostname: The primary host involved.
    - Arg user: The primary user involved.
    - Arg severity: The severity of the alert (e.g., 'Critical', 'High').
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    dataset = os.getenv("BQ_DATASET")
    client = bigquery.Client(project=project_id)

    incident_id = f"INC-{str(uuid.uuid4())[:8]}"
    creation_timestamp = datetime.utcnow().isoformat()

    insert_query = f"""
        INSERT INTO `{project_id}.{dataset}.incident_management`
        (IncidentID, CreationTimestamp, AlertType, Status, Severity, PrimaryHost, PrimaryUser)
        VALUES
        (@incident_id, @creation_timestamp, @alert_type, 'Triage', @severity, @hostname, @user)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("incident_id", "STRING", incident_id),
            bigquery.ScalarQueryParameter(
                "creation_timestamp", "TIMESTAMP", creation_timestamp
            ),
            bigquery.ScalarQueryParameter("alert_type", "STRING", alert_type),
            bigquery.ScalarQueryParameter("severity", "STRING", severity),
            bigquery.ScalarQueryParameter("hostname", "STRING", hostname),
            bigquery.ScalarQueryParameter("user", "STRING", user),
        ]
    )

    try:
        client.query(
            insert_query, job_config=job_config
        ).result()  # Wait for the job to complete
        logger.info(f"Successfully created incident {incident_id}")
        return json.dumps({"status": "success", "incident_id": incident_id})
    except Exception as e:
        logger.error(f"Failed to create incident: {e}")
        return json.dumps({"status": "error", "message": str(e)})
