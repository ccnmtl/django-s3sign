from __future__ import unicode_literals

import json
from datetime import datetime

from django.test import TestCase, RequestFactory, override_settings
from django.utils.encoding import smart_str
from s3sign.views import SignS3View


class PinnedView(SignS3View):
    """ override the fidgety bits to make the main stuff
    easier to test """
    def get_aws_access_key(self):
        return "foo"

    def get_aws_secret_key(self):
        return "bar"

    def get_bucket(self):
        return "bucket"

    @staticmethod
    def now():
        return datetime(year=2016, month=1, day=1)

    @staticmethod
    def now_time():
        return 0

    @staticmethod
    def basename():
        return "f495f780-5fd3-45d3-9483-becc7ebff922"


class TestView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.maxDiff = None

    def test_now(self):
        v = SignS3View()
        self.assertIsNotNone(v.now())

    def test_now_time(self):
        v = SignS3View()
        self.assertIsNotNone(v.now_time())

    def test_basename(self):
        v = SignS3View()
        self.assertIsNotNone(v.basename())

    def test_extension_from_mimetype(self):
        v = SignS3View()
        self.assertEqual(v.extension_from_mimetype('image/jpeg'), '.jpg')
        self.assertEqual(v.extension_from_mimetype('image/png'), '.png')
        self.assertEqual(v.extension_from_mimetype('unknown'), '.obj')

    def test_get_mimetype(self):
        request = self.factory.get("/", dict(s3_object_type='hello'))
        v = SignS3View()
        self.assertEqual(v.get_mimetype(request), 'hello')

    def test_get_name_field(self):
        v = SignS3View()
        self.assertIsNotNone(v.get_name_field())

    @override_settings(AWS_ACCESS_KEY='foo')
    def test_get_aws_access_key(self):
        v = SignS3View()
        self.assertEqual(v.get_aws_access_key(), 'foo')

    @override_settings(AWS_SECRET_KEY='foo')
    def test_get_aws_secret_key(self):
        v = SignS3View()
        self.assertEqual(v.get_aws_secret_key(), 'foo')

    @override_settings(AWS_UPLOAD_BUCKET='foo')
    def test_get_aws_bucket(self):
        v = SignS3View()
        self.assertEqual(v.get_bucket(), 'foo')

    def test_get(self):
        v = PinnedView()
        request = self.factory.get(
            "/",
            dict(s3_object_type='image/jpg', s3_object_name='foo.jpg'))
        response = v.get(request)
        self.assertEqual(response.status_code, 200)
        resp = json.loads(smart_str(response.content))
        self.assertTrue('presigned_post_url' in resp.keys())
        self.assertTrue('url' in resp.keys())

        urlObj = resp['presigned_post_url']
        fields = urlObj.get('fields')

        self.assertEqual(urlObj.get('url'), 'https://s3.amazonaws.com/bucket')
        self.assertEqual(
            fields.get('key'),
            '2016/01/01/f495f780-5fd3-45d3-9483-becc7ebff922.obj')
        self.assertEqual(fields.get('x-amz-algorithm'), 'AWS4-HMAC-SHA256')
        self.assertTrue('x-amz-date' in fields)
        self.assertTrue(
            'us-east-1/s3/aws4_request' in fields.get('x-amz-credential'))

        self.assertTrue('x-amz-signature' in fields)

        self.assertEqual(
            resp['url'],
            ("https://bucket.s3.amazonaws.com/2016/01/01/f495f780"
             "-5fd3-45d3-9483-becc7ebff922.obj"))
