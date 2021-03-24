# -*- coding: utf-8 -*-
import dataiku
import pandas
import logging

from dataiku.customrecipe import get_input_names_for_role, get_recipe_config, get_output_names_for_role
from google_calendar_client import GoogleCalendarClient
from dku_common import get_token_from_config, get_iso_format


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='google-calendar plugin %(levelname)s - %(message)s')


input_A_names = get_input_names_for_role('input_A_role')
config = get_recipe_config()
dku_flow_variables = dataiku.get_flow_variables()

calendar_id_column = config.get("calendar_id_column", None)
from_date_column = config.get("from_date_column", None)
to_date_column = config.get("to_date_column", None)
access_token = get_token_from_config(config)
client = GoogleCalendarClient(config.get("oauth_credentials").get("access_token"))

input_parameters_dataset = dataiku.Dataset(input_A_names[0])
input_parameters_dataframe = input_parameters_dataset.get_dataframe()
events = []
for index, input_parameters_row in input_parameters_dataframe.iterrows():
    calendar_id = input_parameters_row.get(calendar_id_column) if calendar_id_column else "primary"
    from_date = get_iso_format(input_parameters_row.get(from_date_column)) if from_date_column else None
    to_date = get_iso_format(input_parameters_row.get(to_date_column)) if to_date_column else None

    events.extend(
        client.get_events(from_date=from_date, to_date=to_date, calendar_id=calendar_id, can_raise=False)
    )

output_names_stats = get_output_names_for_role('api_output')
odf = pandas.DataFrame(events)

if odf.size > 0:
    api_output = dataiku.Dataset(output_names_stats[0])
    api_output.write_with_schema(odf)
