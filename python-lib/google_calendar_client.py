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
        credentials = Credentials(token, SCOPES)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                raise GoogleCalendarClientError("Credential not valid or need to be refreshed")
        self.service = build('calendar', 'v3', credentials=credentials)

    def get_events(self, from_date, to_date=None, calendar_id="primary", records_limit=-1, can_raise=True):
        if from_date is None:
            from_date = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        kwargs = {
            "calendarId": calendar_id,
            "timeMin": from_date,
            "singleEvents": True,
            "orderBy": "startTime"
        }
        if to_date:
            kwargs["timeMax"] = to_date
        if records_limit > 0:
            kwargs["maxResults"] = records_limit

        try:
            events_result = self.service.events().list(
                **kwargs
            ).execute()
        except Exception as err:
            logging.error("Google Calendar client error : {}".format(err))
            if can_raise:
                raise GoogleCalendarClientError("Error: {}".format(err))
            else:
                return [{"api_error": "{}".format(err)}]
        events = events_result.get('items', [])
        return events
