import logging
import datetime
from dataiku.connector import Connector
from google_calendar_client import GoogleCalendarClient
from dku_common import get_token_from_config, assert_no_temporal_paradox, extract_start_end_date
from dku_constants import DKUConstants as constants


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='google-calendar plugin %(levelname)s - %(message)s')


class GoogleCalendarEventConnector(Connector):

    def __init__(self, config, plugin_config):
        Connector.__init__(self, config, plugin_config)
        access_token = get_token_from_config(config)
        self.client = GoogleCalendarClient(access_token)
        self.from_date = self.config.get("from_date", None)
        self.to_date = self.config.get("to_date", None)
        assert_no_temporal_paradox(self.from_date, self.to_date)
        self.calendar_id = self.config.get("calendar_id", constants.DEFAULT_CALENDAR_ID)
        self.raw_results = self.config.get("raw_results", False)

    def get_read_schema(self):
        # In this example, we don't specify a schema here, so DSS will infer the schema
        # from the columns actually returned by the generate_rows method
        return None

    def generate_rows(self, dataset_schema=None, dataset_partitioning=None,
                      partition_id=None, records_limit=constants.RECORDS_NO_LIMIT):
        first_call = True
        while first_call or self.client.has_more_events():
            first_call = False
            events = self.client.get_events(
                from_date=self.from_date,
                to_date=self.to_date,
                calendar_id=self.calendar_id,
                records_limit=records_limit
            )
            for event in events:
                yield {"api_output": event} if self.raw_results else extract_start_end_date(event)

    def get_writer(self, dataset_schema=None, dataset_partitioning=None,
                   partition_id=None):
        """
        Returns a writer object to write in the dataset (or in a partition).

        The dataset_schema given here will match the the rows given to the writer below.

        Note: the writer is responsible for clearing the partition, if relevant.
        """
        raise NotImplementedError

    def get_partitioning(self):
        """
        Return the partitioning schema that the connector defines.
        """
        raise NotImplementedError

    def list_partitions(self, partitioning):
        """Return the list of partitions for the partitioning scheme
        passed as parameter"""
        return []

    def partition_exists(self, partitioning, partition_id):
        """Return whether the partition passed as parameter exists

        Implementation is only required if the corresponding flag is set to True
        in the connector definition
        """
        raise NotImplementedError

    def get_records_count(self, partitioning=None, partition_id=None):
        """
        Returns the count of records for the dataset (or a partition).

        Implementation is only required if the corresponding flag is set to True
        in the connector definition
        """
        raise NotImplementedError
