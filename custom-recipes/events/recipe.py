# -*- coding: utf-8 -*-
import dataiku
import pandas
import logging

from dataiku.customrecipe import get_input_names_for_role, get_recipe_config, get_output_names_for_role
from google_calendar_client import GoogleCalendarClient
from dku_common import get_token_from_config, get_iso_format
from dku_constants import DKUConstants as constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='google-calendar plugin %(levelname)s - %(message)s')


logger.info("Google Calendar Plugin events recipe")
input_A_names = get_input_names_for_role('input_A_role')
config = get_recipe_config()
dku_flow_variables = dataiku.get_flow_variables()

calendar_id_column = config.get("calendar_id_column", None)
from_date_column = config.get("from_date_column", None)
to_date_column = config.get("to_date_column", None)
access_token = get_token_from_config(config)
logger.info("Retrieving Google Calendar events using columns id '{}', from '{}' to '{}'".format(calendar_id_column, from_date_column, to_date_column))
client = GoogleCalendarClient(access_token)
logger.info("Google Calendar client authenticated")

input_parameters_dataset = dataiku.Dataset(input_A_names[0])
input_parameters_dataframe = input_parameters_dataset.get_dataframe()
logger.info("{} line(s) to process".format(len(input_parameters_dataframe)))
events = []
for index, input_parameters_row in input_parameters_dataframe.iterrows():
    calendar_id = input_parameters_row.get(calendar_id_column, constants.DEFAULT_CALENDAR_ID)
    from_date = get_iso_format(input_parameters_row.get(from_date_column)) if from_date_column else None
    to_date = get_iso_format(input_parameters_row.get(to_date_column)) if to_date_column else None

    first_call = True
    while first_call or client.has_more_events():
        first_call = False
        events.extend(
            client.get_events(from_date=from_date, to_date=to_date, calendar_id=calendar_id, can_raise=False)
        )

odf = pandas.DataFrame(events)

if odf.size > 0:
    output_names_stats = get_output_names_for_role('api_output')
    api_output = dataiku.Dataset(output_names_stats[0])
    api_output.write_with_schema(odf)
