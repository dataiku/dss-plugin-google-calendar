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


def get_date_range(config):
    from datetime import datetime, timedelta
    TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    # "%Y-%m-%dT%H:%M:%S.000"
    #  output format should be 2024-12-31T23:59:00.000
    date_range = config.get("date_range", None)  # Custom by default
    if date_range is None:  # not is_date_entered_manually:
        start_date = config.get("from_date")
        end_date = config.get("to_date")
    elif date_range == "manual":
        start_date = config.get("manual_start_date")
        end_date = config.get("manual_end_date")
    elif date_range == "today":
        today = datetime.now() - timedelta(days=0)
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = today.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "tomorrow":
        now = datetime.now()
        start_of_tomorrow = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_of_tomorrow = start_of_tomorrow.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        start_date = start_of_tomorrow.strftime(TIME_FORMAT)
        end_date = end_of_tomorrow.strftime(TIME_FORMAT)
    elif date_range == "yesterday":
        yesterday = datetime.now() - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = yesterday.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "last_7_days":
        today = datetime.now()
        start_day = today - timedelta(days=7)
        end_day = today - timedelta(days=1)
        start_date = start_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = end_day.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "last_14_days":
        today = datetime.now()
        start_day = today - timedelta(days=14)
        end_day = today - timedelta(days=1)
        start_date = start_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = end_day.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "last_work_week":
        today = datetime.now()
        current_monday = today - timedelta(days=today.weekday())
        last_monday = current_monday - timedelta(days=7)
        last_friday = last_monday + timedelta(days=4)
        start_date = last_monday.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = last_friday.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "last_week":
        today = datetime.now()
        current_monday = today - timedelta(days=today.weekday())
        last_monday = current_monday - timedelta(days=7)
        last_sunday = last_monday + timedelta(days=6)
        start_date = last_monday.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = last_sunday.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "next_week":
        today = datetime.now()
        start_of_next_week = (today - timedelta(days=today.weekday()) + timedelta(days=7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_of_next_week = (start_of_next_week + timedelta(days=6)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        start_date = start_of_next_week.strftime(TIME_FORMAT)
        end_date = end_of_next_week.strftime(TIME_FORMAT)
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
        start_date = start_of_next_month.strftime(TIME_FORMAT)
        end_date = end_of_next_month.strftime(TIME_FORMAT)
    elif date_range == "last_30_days":
        today = datetime.now()
        start_day = today - timedelta(days=30)
        end_day = today - timedelta(days=1)
        start_date = start_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = end_day.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "last_60_days":
        today = datetime.now()
        start_day = today - timedelta(days=60)
        end_day = today - timedelta(days=1)
        start_date = start_day.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = end_day.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "last_month":
        today = datetime.now()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        start_date = first_day_last_month.replace(hour=0, minute=0, second=0, microsecond=0).strftime(TIME_FORMAT)
        end_date = last_day_last_month.replace(hour=23, minute=59, second=0, microsecond=0).strftime(TIME_FORMAT)
    elif date_range == "last_quarter":
        today = datetime.now()
        current_quarter = (today.month - 1) // 3 + 1
        current_year = today.year
        if current_quarter == 1:
            last_quarter = 4
            year_of_last_quarter = current_year - 1
        else:
            last_quarter = current_quarter - 1
            year_of_last_quarter = current_year
        start_month = (last_quarter - 1) * 3 + 1
        end_month = start_month + 2
        start_date = datetime(year_of_last_quarter, start_month, 1, 0, 0, 0).strftime(TIME_FORMAT)
        if end_month == 12:
            end_date_dt = datetime(year_of_last_quarter, 12, 31, 23, 59, 0)
        else:
            first_day_after_quarter = datetime(year_of_last_quarter, end_month + 1, 1)
            end_date_dt = first_day_after_quarter - timedelta(days=1)
            end_date_dt = end_date_dt.replace(hour=23, minute=59, second=0, microsecond=0)
        end_date = end_date_dt.strftime(TIME_FORMAT)
    elif date_range == "last_year":
        today = datetime.now()
        last_year = today.year - 1
        start_date = datetime(last_year, 1, 1, 0, 0, 0).strftime(TIME_FORMAT)
        end_date = datetime(last_year, 12, 31, 23, 59, 0).strftime(TIME_FORMAT)
    return start_date, end_date
