import json
import os

import boto3

from usecase.certificate_usecase import CertificateUsecase
from utils.logger import logger

CERTIFICATE_QUEUE = os.getenv('CERTIFICATE_QUEUE')
SQS = boto3.client('sqs')


def generate_certificate_handler(event, context):
    _ = context
    certificate_usecase = CertificateUsecase()
    for record in event['Records']:
        logger.info(record)
        message_body = json.loads(record['body'])
        event_id = message_body['eventId']
        certificate_usecase.generate_certficates(event_id=event_id)
        SQS.delete_message(QueueUrl=CERTIFICATE_QUEUE, ReceiptHandle=record['receiptHandle'])
