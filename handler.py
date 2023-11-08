import json
import os

import boto3

CERTIFICATE_QUEUE = os.getenv('CERTIFICATE_QUEUE')
SQS = boto3.client('sqs')


def generate_certificate_handler(event, context):
    _ = context
    for record in event['Records']:
        message_body = json.loads(record['body'])
        SQS.delete_message(QueueUrl=CERTIFICATE_QUEUE, ReceiptHandle=record['receiptHandle'])
