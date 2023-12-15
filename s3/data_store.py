import io
import logging
import os
import zipfile
from http import HTTPStatus
from typing import List

from boto3 import client as boto3_client

from s3.exceptions import PdfServiceInternalError
from s3.s3_constants import PresignedURLMethod
from utils.logger import logger


# pylint: disable=broad-except
class S3DataStore:
    __slots__ = ['__s3_client', '__bucket_name', '__logger']

    def __init__(self, bucket_name=os.environ['S3_BUCKET']):
        self.__s3_client = boto3_client('s3')
        self.__bucket_name = bucket_name

    def upload_file(self, file_name: str, object_name: str = None, verbose: bool = True) -> bool:
        result = True

        # If S3 object_name was not specified, use file_name
        if object_name is None:
            object_name = file_name

        try:
            self.__s3_client.upload_file(file_name, self.__bucket_name, object_name)
            if verbose:
                logger.info('Stored file in S3: %s/%s', self.__bucket_name, object_name)
        except Exception as e:
            message = f'Failed to upload file ({file_name}) to S3, Reason: {type(e).__name__} - {str(e)}'
            logger.error(message)
            raise PdfServiceInternalError(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, message=message) from e

        return result

    def download_file(self, object_name: str, file_name: str, verbose: bool = True) -> bool:
        result = True

        try:
            self.__s3_client.download_file(self.__bucket_name, object_name, file_name)
            if verbose:
                logger.info('Downloaded file in S3: %s/%s', self.__bucket_name, object_name)
        except Exception as e:
            message = f'Failed to download file ({object_name}) from S3, Reason: {type(e).__name__} - {str(e)}'
            logger.error(message)
            raise PdfServiceInternalError(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, message=message) from e

        return result

    def zip_files(self, bucket_keys: List[str], output_zip_key: str, verbose: bool = True):
        try:
            # Create an in-memory zip file
            zip_buffer = io.BytesIO()

            # Create a new ZipFile object
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Iterate over the files and add them to the zip
                for key in bucket_keys:
                    # Read and add the file to the zip buffer
                    content = self.__s3_client.get_object(Bucket=self.__bucket_name, Key=key)
                    zip_file.writestr(key.split('/')[-1], content['Body'].read())

            # Upload the zip file to S3
            self.__s3_client.put_object(Body=zip_buffer.getvalue(), Bucket=self.__bucket_name, Key=output_zip_key)

            if verbose:
                logger.info('Stored file in S3: %s', f'{self.__bucket_name}/{output_zip_key}')
        except Exception as e:
            message = f'Failed to zip files, Reason: {type(e).__name__} - {str(e)}'
            logger.error(message)
            raise PdfServiceInternalError(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, message=message) from e

    def generate_presigned_url(
        self,
        object_name: str,
        method: PresignedURLMethod,
        expires_in: int = 3600,
        content_type: str = None,
    ) -> str:
        try:
            params = {'Bucket': self.__bucket_name, 'Key': object_name}
            if method == PresignedURLMethod.PUT_OBJECT:
                params['ContentType'] = content_type

            url = self.__s3_client.generate_presigned_url(
                ClientMethod=method.value, Params=params, ExpiresIn=expires_in
            )
            logger.info('Pre-signed URL generated for file: %s', object_name)
        except Exception as e:
            message = (
                f'Failed to generate pre-signed URl for file: ({object_name}), '
                f'Reason: '
                f'{type(e).__name__} - {str(e)}'
            )
            logger.error(message)
            raise PdfServiceInternalError(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, message=message) from e

        return url

    def get_files(self, directory_name: str):
        return self.__s3_client.list_objects_v2(Bucket=self.__bucket_name, Prefix=directory_name)['Contents']

    def delete_file(self, object_name: str):
        try:
            self.__s3_client.delete_object(Bucket=self.__bucket_name, Key=object_name)
        except Exception as e:
            logger.error('Failed to delete file (%s), Reason: %s - %s', object_name, type(e).__name__, str(e))
            return False

        return True

    def get_file(self, object_key):
        try:
            s3_response = self.__s3_client.get_object(Bucket=self.__bucket_name, Key=object_key)
        except Exception as e:
            logger.error('Failed to get file (%s), Reason: %s - %s', object_key, type(e).__name__, str(e))
            return None

        return s3_response['Body'].read()

    def is_file_existing(self, path: str) -> bool:
        """Check S3 bucket if file is existing."""
        if not path:
            return False
        return bool(self.get_file(object_key=path))

    def copy_object(self, src_bucket, src_key, target_key):
        try:
            self.__s3_client.copy_object(
                CopySource={'Bucket': src_bucket, 'Key': src_key}, Bucket=self.__bucket_name, Key=target_key
            )
        except Exception as e:
            logger.error('Failed to get copy (%s), Reason: %s - %s', src_key, type(e).__name__, str(e))
            return
