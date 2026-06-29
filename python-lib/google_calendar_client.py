import logging
from urllib.parse import unquote
import requests
from dku_constants import DKUConstants as constants


CALENDAR_API_BASE_URL = "https://www.googleapis.com/calendar/v3"


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='google-calendar plugin %(levelname)s - %(message)s')


class GoogleCalendarClientError(ValueError):
    pass


class GoogleCalendarClient():
    def __init__(self, token):
        logger.info("GoogleCalendarClient init")
        if not token:
            raise GoogleCalendarClientError("Credential not valid or need to be refreshed")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": "Bearer {}".format(token),
            "Accept": "application/json"
        })
        logger.info("Google Calendar HTTP session ready")
        self.next_page_token = None
        self.number_retrieved_events = 0

    def get_events(self, from_date=None, to_date=None, calendar_id=constants.DEFAULT_CALENDAR_ID, records_limit=constants.RECORDS_NO_LIMIT, can_raise=True):
        params = self.get_event_kwargs(from_date, to_date, records_limit)
        try:
            events_result = self._request(
                "GET",
                "/calendars/{}/events".format(self._encode_calendar_id(calendar_id)),
                params=params
            )
        except GoogleCalendarClientError as err:
            error_message = str(err)
            logging.error("Google Calendar client error : {}".format(error_message))
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

    def get_event_kwargs(self, from_date=None, to_date=None, records_limit=constants.RECORDS_NO_LIMIT):
        params = {
            "singleEvents": True,
            "orderBy": "startTime"
        }
        if from_date:
            params["timeMin"] = from_date
        if to_date:
            params["timeMax"] = to_date
        if records_limit > 0:
            params["maxResults"] = records_limit
        if self.next_page_token:
            params["pageToken"] = self.next_page_token
        return params

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

        response = self._request(
            "POST",
            "/calendars/{}/events".format(self._encode_calendar_id(calendar_id)),
            json=event
        )
        return response.get("htmlLink")

    def _request(self, method, path, params=None, json=None):
        url = "{}{}".format(CALENDAR_API_BASE_URL, path)
        try:
            response = self.session.request(method, url, params=params, json=json, timeout=30)
        except requests.RequestException as err:
            raise GoogleCalendarClientError(str(err))

        if response.ok:
            return response.json()

        error_message = self._build_error_message(response)
        raise GoogleCalendarClientError(error_message)

    def _build_error_message(self, response):
        try:
            payload = response.json()
        except ValueError:
            payload = {}

        error = payload.get("error", {})
        if response.status_code == 404:
            return "The calendar with ID '{}' does not exists.".format(
                self._extract_calendar_id_from_response(response)
            )

        message = error.get("message") or response.text or "HTTP {}".format(response.status_code)
        return "HTTP {}: {}".format(response.status_code, message)

    def _extract_calendar_id_from_response(self, response):
        marker = "/calendars/"
        path = response.request.path_url
        if marker not in path:
            return constants.DEFAULT_CALENDAR_ID
        encoded_calendar_id = path.split(marker, 1)[1].split("/events", 1)[0]
        return unquote(encoded_calendar_id)

    def _encode_calendar_id(self, calendar_id):
        return requests.utils.quote(calendar_id, safe="")
