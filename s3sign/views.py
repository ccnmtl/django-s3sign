from __future__ import unicode_literals

import json
import time
import uuid

import boto3

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from django.utils import timezone

from s3sign.utils import s3_config, upload_file


DEFAULT_AWS_REGION = 'us-east-1'


class SignS3View(View):
    name_field = 's3_object_name'
    type_field = 's3_object_type'
    expiration_time = 3600 * 8  # 8 hours
    mime_type_extensions = [
        ('bmp', '.bmp'),
        ('gif', '.gif'),
        ('jpeg', '.jpg'),
        ('pdf', '.pdf'),
        ('png', '.png'),
        ('svg', '.svg'),
        ('webp', '.webp'),
        ('heif', '.heif'),
        ('heic', '.heic'),
        ('avif', '.avif'),
    ]
    default_extension = '.obj'
    root = ''
    path_string = (
        "{root}{now.year:04d}/{now.month:02d}/"
        "{now.day:02d}/{basename}{extension}")
    acl = 'public-read'
    max_file_size = 2000000000  # 2gb

    # The private flag specifies whether we need to return a signed
    # GET url when the upload succeeds.
    private = False

    aws_region_name = DEFAULT_AWS_REGION
    if hasattr(settings, 'AWS_S3_REGION_NAME'):
        aws_region_name = settings.AWS_S3_REGION_NAME

    def dispatch(self, request, *args, **kwargs):
        self.s3_client = boto3.client(
            's3', config=s3_config,
            region_name=self.aws_region_name,
            aws_access_key_id=self.get_aws_access_key(),
            aws_secret_access_key=self.get_aws_secret_key()
        )
        return super().dispatch(request, *args, **kwargs)

    def get_name_field(self) -> str:
        return self.name_field

    def get_type_field(self) -> str:
        return self.type_field

    def get_expiration_time(self):
        return self.expiration_time

    def get_mime_type_extensions(self) -> list:
        return self.mime_type_extensions

    def get_default_extension(self) -> str:
        return self.default_extension

    def get_root(self) -> str:
        return self.root

    def get_path_string(self) -> str:
        return self.path_string

    def get_aws_access_key(self) -> str:
        return settings.AWS_ACCESS_KEY

    def get_aws_secret_key(self) -> str:
        return settings.AWS_SECRET_KEY

    def get_bucket(self) -> str:
        return settings.AWS_UPLOAD_BUCKET

    def get_mimetype(self, request):
        return request.GET.get(self.get_type_field())

    def extension_from_mimetype(self, mime_type):
        for m, ext in self.get_mime_type_extensions():
            if m in mime_type:
                return ext
        return self.get_default_extension()

    @staticmethod
    def now():
        return timezone.now()

    @staticmethod
    def now_time():
        return time.time()

    @staticmethod
    def basename():
        return str(uuid.uuid4())

    def extension(self, request):
        return self.extension_from_mimetype(self.get_mimetype(request))

    def get_object_name(self, request):
        now = self.now()
        basename = self.basename()
        extension = self.extension(request)
        return self.get_path_string().format(
            now=now, basename=basename, extension=extension,
            root=self.get_root())

    def get(self, request):
        if not getattr(self, 's3_client', None):
            self.s3_client = boto3.client(
                's3', config=s3_config,
                region_name=self.aws_region_name,
                aws_access_key_id=self.get_aws_access_key(),
                aws_secret_access_key=self.get_aws_secret_key()
            )

        data = upload_file(
            self.s3_client, self.get_bucket(), self.get_mimetype(request),
            self.get_object_name(request), self.max_file_size, self.acl,
            self.get_expiration_time(), self.private)

        return HttpResponse(
            json.dumps(data), content_type='application/json')
