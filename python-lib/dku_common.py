import pandas
import datetime
from dku_constants import DKUConstants as constants


def get_token_from_config(config):
    oauth_credentials = config.get("oauth_credentials")
    if not oauth_credentials:
        raise ValueError("OAuth credential not present. Please refer to the plugin's documentation.")
    access_token = oauth_credentials.get("access_token")
    if not access_token:
        raise ValueError("No access token. Please validate the Google Calendar preset in your profile's credentials list. ")
    if isinstance(access_token, dict):
        raise ValueError("The 'Manually defined' option cannot be used for Single Sign On authentication. Please create a preset in the plugin's settings, then validate it in your profile's credentials list.")
    return access_token


def get_iso_format(panda_date):
    if pandas.isnull(panda_date):
        return None
    return panda_date.isoformat() + "Z"


def get_datetime_from_iso_string(iso_string):
    return datetime.datetime.strptime(iso_string, constants.ISO_DATE_FORMAT)


def assert_no_temporal_paradox(from_date, to_date):
    if from_date and to_date:
        from_datetime = get_datetime_from_iso_string(from_date)
        to_datetime = get_datetime_from_iso_string(to_date)
        if from_datetime > to_datetime:
            raise ValueError("The 'To' date currently set is before the 'From' date")


def extract_start_end_date(event):
    start = event.pop("start", None)
    if start:
        event["start_dateTime"] = start.get("dateTime")
        event["start_timeZone"] = start.get("timeZone", "")
    end = event.pop("end", None)
    if end:
        event["end_dateTime"] = end.get("dateTime")
        event["end_timeZone"] = end.get("timeZone", "")
    return event


def extract_start_end_dates(events):
    for event in events:
        event = extract_start_end_date(event)
    return events


def time_now_RFC3339():
    now = datetime.datetime.now(datetime.timezone.utc)
    return now.isoformat("T").split(".")[0] + "Z"
