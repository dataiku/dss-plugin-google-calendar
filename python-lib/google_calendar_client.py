import logging
import datetime
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


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
        self.records = 0

    def get_events(self, from_date=None, to_date=None, calendar_id="primary", records_limit=-1, can_raise=True):
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
        try:
            events_result = self.service.events().list(
                **kwargs
            ).execute()
        except Exception as err:
            logging.error("Google Calendar client error : {}".format(err))
            self.next_page_token = None
            if can_raise:
                raise GoogleCalendarClientError("Error: {}".format(err))
            else:
                return [{"api_error": "{}".format(err)}]
        events = events_result.get('items', [])
        self.records += len(events)
        logger.info("{} events retrieved, {} in total".format(len(events), self.records))

        if records_limit > 0:  # I know. But headache.
            if self.records < records_limit:
                self.next_page_token = events_result.get("nextPageToken")
            else:
                self.next_page_token = None
        else:
            self.next_page_token = events_result.get("nextPageToken")

        if self.next_page_token:
            logging.info("More events available")
        return events

    def has_more_events(self):
        return self.next_page_token is not None
