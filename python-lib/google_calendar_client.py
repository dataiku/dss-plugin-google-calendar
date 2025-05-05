import logging
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dku_constants import DKUConstants as constants


SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='google-calendar plugin %(levelname)s - %(message)s')


class GoogleCalendarClientError(ValueError):
    pass


class GoogleCalendarClient():
    def __init__(self, token):
        logger.info("GoogleCalendarClient init")
        credentials = Credentials(token, SCOPES)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                raise GoogleCalendarClientError("Credential not valid or need to be refreshed")
        logger.info("Google credentials retrieved")
        self.service = build('calendar', 'v3', credentials=credentials)
        logger.info("Google Calendar service ok")
        self.next_page_token = None
        self.number_retrieved_events = 0

    def get_events(self, from_date=None, to_date=None, calendar_id=constants.DEFAULT_CALENDAR_ID, records_limit=constants.RECORDS_NO_LIMIT, can_raise=True):

        kwargs = self.get_event_kwargs(from_date, to_date, calendar_id, records_limit)
        try:
            events_result = self.service.events().list(
                **kwargs
            ).execute()
        except Exception as err:
            error_message = "{}".format(err)
            logging.error("Google Calendar client error : {}".format(error_message))
            if error_message.startswith("<HttpError 404"):
                error_message = "The calendar with ID '{}' does not exists.".format(calendar_id)
            self.next_page_token = None
            if can_raise:
                raise GoogleCalendarClientError("Error: {}".format(error_message))
            else:
                return [{"api_error": "{}".format(error_message)}]

        events = events_result.get('items', [])
        self.number_retrieved_events += len(events)
        logger.info("{} events retrieved, {} in total".format(len(events), self.number_retrieved_events))

        self.update_next_page_token(events_result, records_limit)

        return events

    def get_event_kwargs(self, from_date=None, to_date=None, calendar_id=constants.DEFAULT_CALENDAR_ID, records_limit=constants.RECORDS_NO_LIMIT):
        kwargs = {
            "calendarId": calendar_id,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        if from_date:
            kwargs["timeMin"] = from_date
        if to_date:
            kwargs["timeMax"] = to_date
        if records_limit > 0:
            kwargs["maxResults"] = records_limit
        if self.next_page_token:
            kwargs["pageToken"] = self.next_page_token
        return kwargs

    def update_next_page_token(self, events_result, records_limit=constants.RECORDS_NO_LIMIT):
        if records_limit == constants.RECORDS_NO_LIMIT or self.number_retrieved_events < records_limit:
            self.next_page_token = events_result.get("nextPageToken")
        else:
            self.next_page_token = None

        if self.next_page_token:
            logging.info("More events available")

    def has_more_events(self):
        return self.next_page_token is not None

    def create_event(self, **kwargs):
        calendar_id = kwargs.get("calendar_id", constants.DEFAULT_CALENDAR_ID)
        event = {}
        event["summary"] = kwargs.get("summary", "")
        event["location"] = kwargs.get("location", "")
        event["description"] = kwargs.get("description", "")
        event["attendees"] = kwargs.get("attendees", "")
        event["start"] = {
            'dateTime': kwargs.get("start")
        }
        event["end"] = {
            'dateTime': kwargs.get("end")
        }

        response = self.service.events().insert(calendarId=calendar_id, body=event).execute()
        return response.get("htmlLink")
