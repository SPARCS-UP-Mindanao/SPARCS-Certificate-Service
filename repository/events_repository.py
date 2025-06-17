import logging
import os
from datetime import datetime
from http import HTTPStatus
from typing import List, Tuple

from constants.common_constants import EntryStatus
from model.events.event import Event
from pynamodb.connection import Connection
from pynamodb.exceptions import (
    PynamoDBConnectionError,
    QueryError,
    TableDoesNotExist,
)


class EventsRepository:
    def __init__(self) -> None:
        self.core_obj = 'Event'
        self.current_date = datetime.utcnow().isoformat()
        self.latest_version = 0
        self.conn = Connection(region=os.getenv('REGION'))

    def query_events(self, event_id: str = None) -> Tuple[HTTPStatus, List[Event], str]:
        try:
            range_key_condition = Event.eventId == event_id if event_id else None
            event_entries = list(
                Event.eventIdIndex.query(
                    hash_key=f'v{self.latest_version}',
                    range_key_condition=range_key_condition,
                    filter_condition=Event.entryStatus == EntryStatus.ACTIVE.value,
                )
            )
            if not event_entries:
                if event_id:
                    message = f'Event with ID={event_id} not found'
                    logging.error(f'[{self.core_obj}={event_id}] {message}')
                else:
                    message = 'No events found'
                    logging.error(f'[{self.core_obj}] {message}')

                return HTTPStatus.NOT_FOUND, None, message

        except QueryError as e:
            message = f'Failed to query event: {str(e)}'
            logging.error(f'[{self.core_obj}={event_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message
        except TableDoesNotExist as db_error:
            message = f'Error on Table, Please check config to make sure table is created: {str(db_error)}'
            logging.error(f'[{self.core_obj}={event_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except PynamoDBConnectionError as db_error:
            message = f'Connection error occurred, Please check config(region, table name, etc): {str(db_error)}'
            logging.error(f'[{self.core_obj}={event_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message
        else:
            if event_id:
                logging.info(f'[{self.core_obj}={event_id}] Fetch Event data successful')
                return HTTPStatus.OK, event_entries[0], None

            logging.info(f'[{self.core_obj}={event_id}] Fetch Event data successful')
            return HTTPStatus.OK, event_entries, None
