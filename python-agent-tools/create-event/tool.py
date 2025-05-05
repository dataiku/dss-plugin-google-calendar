import logging
from dataiku.llm.agent_tools import BaseAgentTool
from google_calendar_client import GoogleCalendarClient
from dku_common import (
    get_token_from_config, assert_no_temporal_paradox, extract_start_end_date, time_now_RFC3339
)
from dku_constants import DKUConstants as constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='google-calendar create event tools plugin %(levelname)s - %(message)s')


class CreateGoogleCalendarEventsTool(BaseAgentTool):

    def set_config(self, config, plugin_config):
        self.config = config
        access_token = get_token_from_config(config)
        self.client = GoogleCalendarClient(access_token)
        self.calendar_id = config.get("calendar_id", constants.DEFAULT_CALENDAR_ID)

    def get_descriptor(self, tool):
        time_now = "All time expression should be evaluated agains the current date and time, which is {}.".format(time_now_RFC3339())
        return {
            "description": "This tool is a wrapper around Google Calendar Events list API, useful when you need to create an event stored on a Google Calendar. The input to this tool is a dictionary containing the time period for the events, e.g. '{'timeMin':'2011-06-03T10:00:00Z', 'timeMax':'2011-06-03T10:30:00Z'}'",
            "inputSchema": {
                "$id": "https://dataiku.com/agents/tools/search/input",
                "title": "Create Google Calendar events tool",
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Title of the event"
                    },
                    "location": {
                        "type": "string",
                        "description": "Location of the event"
                    },
                    "description": {
                        "type": "string",
                        "description": "Short description of the event"
                    },
                    "start": {
                        "type": "date",
                        "description": "Upper bound (exclusive) for the event's start time. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z. {}".format(time_now)
                    },
                    "end": {
                        "type": "date",
                        "description": "Lower bound (exclusive) for the event's end time. Must be an RFC3339 timestamp with mandatory time zone offset, for example, 2011-06-03T10:00:00-07:00, 2011-06-03T10:00:00Z. {}".format(time_now)
                    },
                    "attendees": {
                        "type": "string",
                        "description": "Comma separated string of the attendees email addresses"
                    }
                }
            }
        }

    def invoke(self, input, trace):
        logger.info("Invoke google-calendar tool with {}".format(input))
        args = input.get("input", {})

        # Log inputs and config to trace
        trace.span["name"] = "CREATE_GOOGLE_CALENDAR_EVENTS_TOOL_CALL"
        for key, value in args.items():
            trace.inputs[key] = value
        trace.attributes["config"] = self.config

        try:
            attendees_emails = args.get("attendees","").split(",")
            attendees = []
            for email in attendees_emails:
                attendees.append({"email":email})
                
            response = self.client.create_event(
                calendar_id=self.calendar_id,
                summary=args.get("summary"),
                location=args.get("location"),
                description=args.get("description"),
                start=args.get("start"),
                end=args.get("end"),
                attendees = attendees
            )
        except Exception as error:
            logger.error("There was an error {}".format(error))
            return {
                "output": "There was an error and the Google Calendar event could not be created : {}".format(error)
            }

        output_text = "Event created with the following link : {} - {}".format(response, str(attendees))

        # Log outputs to trace
        trace.outputs["output"] = output_text

        return {
            "output": output_text
        }
