import logging
import os
import uuid
from botocore.config import Config
from botocore.exceptions import ClientError


DEFAULT_AWS_REGION = 'us-east-1'
PATH_STRING = (
    '{root}{now.year:04d}/{now.month:02d}/'
    '{now.day:02d}/{basename}{extension}')


def get_object_name(now, extension, root=''):
    basename = str(uuid.uuid4())
    return PATH_STRING.format(
        now=now, basename=basename, extension=extension, root=root)


s3_config = Config(
    signature_version='s3v4',
    s3={'addressing_style': 'path'},
)


def create_presigned_url(s3_client, bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    From: https://boto3.amazonaws.com/v1/documentation/api/latest/
                             guide/s3-presigned-urls.html

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to
      remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name,
                    'Key': object_name},
            ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


def create_presigned_url_expanded(
        s3_client, client_method_name, method_parameters=None,
        expiration=3600, http_method=None):
    """Generate a presigned URL to invoke an S3.Client method

    Not all the client methods provided in the AWS Python SDK are
    supported.

    :param client_method_name: Name of the S3.Client method, e.g.,
    'list_buckets'

    :param method_parameters: Dictionary of parameters to send to
    the method

    :param expiration: Time in seconds for the presigned URL to
    remain valid

    :param http_method: HTTP method to use (GET, etc.)
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 client method
    try:
        response = s3_client.generate_presigned_url(
            ClientMethod=client_method_name,
            Params=method_parameters,
            ExpiresIn=expiration,
            HttpMethod=http_method)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


def create_presigned_post(s3_client, bucket_name, object_name,
                          fields=None, conditions=None, expiration=3600):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    try:
        response = s3_client.generate_presigned_post(bucket_name,
                                                     object_name,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    return response


def upload_file(s3_client, file_name, bucket, object_name=None) -> bool:
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False

    return True


def prepare_presigned_post(
        s3_client, bucket, mime_type, object_name,
        max_file_size, acl, expiration_time, private
) -> dict:
    """
    Prepare data necessary to make a POST request to upload a file to
    S3 from JavaScript.
    """
    S3_BUCKET = bucket

    url = 'https://{}.s3.amazonaws.com/{}'.format(
        S3_BUCKET, object_name)

    # Prepare post configuration (fields & conditions)
    fields = {
        'Content-Type': mime_type.replace(' ', '+'),
    }
    conditions = [
        # Allow for setting the content-type in the form data.
        ['starts-with', '$Content-Type', ''],
        # Limit upload to self.max_file_size
        ['content-length-range', 0, max_file_size],
    ]

    if acl:
        fields['acl'] = acl
        conditions.append({'acl': acl})

    presigned_post_url = create_presigned_post(
        s3_client, S3_BUCKET, object_name,
        fields=fields,
        conditions=conditions,
        expiration=expiration_time)

    data = {
        'url': url,
        'presigned_post_url': presigned_post_url,
    }

    if private:
        data['presigned_get_url'] = create_presigned_url(
            s3_client, S3_BUCKET,
            object_name, expiration_time
        )

    return data
