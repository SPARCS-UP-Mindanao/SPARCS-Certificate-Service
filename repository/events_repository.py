import logging
import os
from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from typing import List, Tuple

from pynamodb.connection import Connection
from pynamodb.exceptions import (
    PutError,
    PynamoDBConnectionError,
    QueryError,
    TableDoesNotExist,
    TransactWriteError,
)
from pynamodb.transactions import TransactWrite

from constants.common_constants import EntryStatus
from model.events.event import Event, EventIn
from repository.repository_utils import RepositoryUtils


class EventsRepository:
    def __init__(self) -> None:
        self.core_obj = 'Event'
        self.current_date = datetime.utcnow().isoformat()
        self.latest_version = 0
        self.conn = Connection(region=os.getenv('REGION'))

    def query_events(self, event_id: str = None) -> Tuple[HTTPStatus, List[Event], str]:
        try:
            if event_id:
                range_key_prefix = f'v{self.latest_version}#{event_id}'
                range_key_condition = Event.rangeKey.__eq__(range_key_prefix)
            else:
                range_key_prefix = f'v{self.latest_version}#'
                range_key_condition = Event.rangeKey.startswith(range_key_prefix)

            event_entries = list(
                Event.query(
                    hash_key=self.core_obj,
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

    def update_event(self, event_entry: Event, event_in: EventIn) -> Tuple[HTTPStatus, Event, str]:
        current_version = event_entry.latestVersion
        new_version = current_version + 1

        data = RepositoryUtils.load_data(pydantic_schema_in=event_in, exclude_unset=True)
        has_update, updated_data = RepositoryUtils.get_update(
            old_data=RepositoryUtils.db_model_to_dict(event_entry), new_data=data
        )
        if not has_update:
            return HTTPStatus.OK, event_entry, 'no update'
        try:
            with TransactWrite(connection=self.conn) as transaction:
                # Update Entry -----------------------------------------------------------------------------
                # check if there's update or none
                updated_data.update(
                    updateDate=self.current_date,
                    updatedBy=os.getenv('CURRENT_USER'),
                    latestVersion=new_version,
                )
                actions = [getattr(Event, k).set(v) for k, v in updated_data.items()]
                transaction.update(event_entry, actions=actions)

                # Store Old Entry --------------------------------------------------------------------------
                old_event_entry = deepcopy(event_entry)
                old_event_entry.rangeKey = event_entry.rangeKey.replace('v0#', f'v{new_version}#')
                old_event_entry.latestVersion = current_version
                old_event_entry.updatedBy = old_event_entry.updatedBy or os.getenv('CURRENT_USER')
                transaction.save(old_event_entry)

            event_entry.refresh()
            logging.info(f'[{event_entry.rangeKey}] ' f'Update event data successful')
            return HTTPStatus.OK, event_entry, ''

        except TransactWriteError as e:
            message = f'Failed to update event data: {str(e)}'
            logging.error(f'[{event_entry.rangeKey}] {message}')

            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

    def delete_event(self, event_entry: Event) -> Tuple[HTTPStatus, str]:
        try:
            # create new entry with old data
            current_version = event_entry.latestVersion
            new_version = current_version + 1
            old_event_entry = deepcopy(event_entry)
            old_event_entry.rangeKey = event_entry.rangeKey.replace('v0#', f'v{new_version}#')
            old_event_entry.updatedBy = old_event_entry.updatedBy or os.getenv('CURRENT_USER')
            old_event_entry.save()

            # set entry status to deleted
            event_entry.updateDate = self.current_date
            event_entry.updatedBy = os.getenv('CURRENT_USER')
            event_entry.latestVersion = new_version
            event_entry.entryStatus = EntryStatus.DELETED.value
            event_entry.save()

            logging.info(f'[{event_entry.rangeKey}] ' f'Delete event data successful')
            return HTTPStatus.OK, None
        except PutError as e:
            message = f'Failed to delete event data: {str(e)}'
            logging.error(f'[{event_entry.rangeKey}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, message

    def update_event_after_s3_upload(self, event_entry: Event, event_in: EventIn) -> Tuple[HTTPStatus, Event, str]:
        """
        This method is almost the same as the update_event() method,
        but excludes the metadata e.g updatedBy, updateDate etc.
        This is needed so that the lambda handler that triggers when a file
        is uploaded on S3 works properly.
        """
        data = RepositoryUtils.load_data(pydantic_schema_in=event_in, exclude_unset=True)
        _, updated_data = RepositoryUtils.get_update(
            old_data=RepositoryUtils.db_model_to_dict(event_entry), new_data=data
        )

        try:
            with TransactWrite(connection=self.conn) as transaction:
                actions = [getattr(Event, k).set(v) for k, v in updated_data.items()]
                transaction.update(event_entry, actions=actions)

            event_entry.refresh()
            logging.info(f'[{event_entry.rangeKey}] ' f'Update event data successful')
            return HTTPStatus.OK, event_entry, ''

        except TransactWriteError as e:
            message = f'Failed to update event data: {str(e)}'
            logging.error(f'[{event_entry.rangeKey}] {message}')

            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message
