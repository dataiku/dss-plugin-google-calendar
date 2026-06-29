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
    if isinstance(panda_date, str):
        return panda_date
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


def get_date_range(config):
    from datetime import datetime, timedelta
    TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    def start_of(date):
        return date.replace(hour=0, minute=0, second=0, microsecond=0)
    def end_of(date):
        return date.replace(hour=23, minute=59, second=59, microsecond=0)
    def today():
        return datetime.now() - timedelta(days=0)
    def yesterday():
        return datetime.now() - timedelta(days=1)
    def tomorrow():
        return datetime.now() + timedelta(days=1)
    def current_monday():
        return today() - timedelta(days=today().weekday())
    date_range = config.get("date_range", None)  # Custom by default
    if date_range is None:  # not is_date_entered_manually:
        start_date = config.get("from_date")
        end_date = config.get("to_date")
    elif date_range == "manual":
        start_date = config.get("manual_start_date")
        end_date = config.get("manual_end_date")
    else:
        if date_range == "today":
            start_date = start_of(today())
            end_date = end_of(today())
        elif date_range == "tomorrow":
            start_date = start_of(tomorrow())
            end_date = end_of(tomorrow())
        elif date_range == "yesterday":
            start_date = start_of(yesterday())
            end_date = end_of(yesterday())
        elif date_range == "last_7_days":
            start_day = today() - timedelta(days=7)
            end_day = today() - timedelta(days=1)
            start_date = start_of(start_day)
            end_date = end_of(end_day)
        elif date_range == "last_14_days":
            start_day = today() - timedelta(days=14)
            end_day = today() - timedelta(days=1)
            start_date = start_of(start_day)
            end_date = end_of(end_day)
        elif date_range == "last_work_week":
            last_monday = current_monday() - timedelta(days=7)
            last_friday = last_monday + timedelta(days=4)
            start_date = start_of(last_monday)
            end_date = end_of(last_friday)
        elif date_range == "last_week":
            last_monday = current_monday() - timedelta(days=7)
            last_sunday = last_monday + timedelta(days=6)
            start_date = start_of(last_monday)
            end_date = end_of(last_sunday)
        elif date_range == "next_week":
            start_date = start_of(current_monday() + timedelta(days=7))
            end_date = end_of((start_date + timedelta(days=6)))
        elif date_range=="next_month":
            now = datetime.now()
            if now.month == 12:
                start_of_next_month = now.replace(
                    year=now.year + 1, month=1, day=1,
                    hour=0, minute=0, second=0, microsecond=0
                )
            else:
                start_of_next_month = now.replace(
                    month=now.month + 1, day=1,
                    hour=0, minute=0, second=0, microsecond=0
                )
            if start_of_next_month.month == 12:
                start_of_following_month = start_of_next_month.replace(
                    year=start_of_next_month.year + 1, month=1
                )
            else:
                start_of_following_month = start_of_next_month.replace(
                    month=start_of_next_month.month + 1
                )
            end_of_next_month = start_of_following_month - timedelta(microseconds=1)
            start_date = start_of_next_month
            end_date = end_of_next_month
        elif date_range == "last_30_days":
            start_day = today() - timedelta(days=30)
            end_day = today() - timedelta(days=1)
            start_date = start_of(start_day)
            end_date = end_of(end_day)
        elif date_range == "last_60_days":
            start_day = today() - timedelta(days=60)
            end_day = today() - timedelta(days=1)
            start_date = start_of(start_day)
            end_date = end_of(end_day)
        elif date_range == "last_month":
            first_day_this_month = today().replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            start_date = start_of(first_day_last_month)
            end_date = end_of(last_day_last_month)
        elif date_range == "last_quarter":
            current_quarter = (today().month - 1) // 3 + 1
            current_year = today().year
            if current_quarter == 1:
                last_quarter = 4
                year_of_last_quarter = current_year - 1
            else:
                last_quarter = current_quarter - 1
                year_of_last_quarter = current_year
            start_month = (last_quarter - 1) * 3 + 1
            end_month = start_month + 2
            start_date = datetime(year_of_last_quarter, start_month, 1, 0, 0, 0)
            if end_month == 12:
                end_date = datetime(year_of_last_quarter, 12, 31, 23, 59, 0)
            else:
                first_day_after_quarter = datetime(year_of_last_quarter, end_month + 1, 1)
                end_date = end_of(first_day_after_quarter - timedelta(days=1))
        elif date_range == "last_year":
            last_year = today().year - 1
            start_date = datetime(last_year, 1, 1, 0, 0, 0)
            end_date = datetime(last_year, 12, 31, 23, 59, 0)
        start_date = start_date.strftime(TIME_FORMAT)
        end_date = end_date.strftime(TIME_FORMAT)
    return start_date, end_date
