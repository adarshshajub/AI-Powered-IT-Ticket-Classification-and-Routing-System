import logging
import requests
from django.conf import settings 
from django.utils import timezone

logger = logging.getLogger(__name__)

servicenow_instance = settings.SERVICENOW_INSTANCE
servicenow_username = settings.SERVICENOW_USERNAME
servicenow_password = settings.SERVICENOW_PASSWORD
servicenow_sys_id = settings.SERVICENOW_SYSID


def create_servicenow_ticket(ticket):

    url = f"https://{servicenow_instance}.service-now.com/api/now/table/incident"
    assignment_group_sys_id =None
    
    if ticket.assigned_team:
        assignment_group_sys_id = ticket.assigned_team.servicenow_group_id

    if ticket.priority.lower() == "critical":
        impact = 1
        urgency =1
    elif ticket.priority.lower() == "high":
        impact = 1
        urgency =2
    elif ticket.priority.lower() == "medium":
        impact = 2
        urgency =2
    else:
        impact = 2
        urgency =3

    print(f"impact: {impact}, urgency: {urgency}")


    payload = {
        "short_description": ticket.title,
        "description": ticket.description,
        "category": ticket.category,
        "caller_id":servicenow_sys_id,
        "impact": impact,
        "urgency": urgency,
        "assignment_group": assignment_group_sys_id,
        "contact_type":"virtual_agent",
    }


    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


    try:
        logger.info(f"Attempting ServiceNow sync for ticket {ticket.id}")


        response = requests.post(
            url,
            json=payload,
            auth=(servicenow_username, servicenow_password),
            timeout=30,
            headers=headers,
        )

        # FORCE HTTP errors to raise exception
        response.raise_for_status()

        data = response.json()

        ticket.servicenow_ticket_number = data.get("result", {}).get("number")
        ticket.servicenow_sys_id = data.get("result", {}).get("sys_id")
        ticket.ticket_creation_status = "created"
        ticket.error_message = None
        ticket.last_sync_attempt = timezone.now()
        ticket.save(update_fields=[
            "servicenow_ticket_number",
            "servicenow_sys_id",
            "ticket_creation_status",
            "error_message",
            "last_sync_attempt"
        ])


        logger.info(
            f"ServiceNow ticket created successfully "
            f"(Ticket ID={ticket.id}, SN={ticket.servicenow_ticket_number})"
        )


        return True


    except requests.exceptions.HTTPError:
        logger.error(
            f"ServiceNow HTTP error for ticket {ticket.id} | "
            f"Status={response.status_code} | Response={response.text}"
        )
        raise


    except requests.exceptions.RequestException:
        logger.error(
            f"Network error while calling ServiceNow for ticket {ticket.id}"
        )
        raise


    except Exception:
        logger.error(
            f"Unexpected error while creating ServiceNow ticket "
            f"(ticket_id={ticket.id})"
        )
        raise


def fetch_servicenow_ticket_status(sys_id: str) -> str | None:
    """
    Fetch latest ServiceNow incident state using sys_id
    """
    url = f"https://{servicenow_instance}.service-now.com/api/now/table/incident/{sys_id}"

    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            url,
            auth=(servicenow_username, servicenow_password),
            timeout=30,
            headers=headers,
        )
        response.raise_for_status()

        data = response.json()
        return data["result"].get("state")

    except Exception:
        logger.exception(f"Failed to fetch ServiceNow status for sys_id={sys_id}")
        return None