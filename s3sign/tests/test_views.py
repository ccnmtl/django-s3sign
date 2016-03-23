from django.test import TestCase, RequestFactory, override_settings
from s3sign.views import SignS3View


class TestView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_now(self):
        v = SignS3View()
        self.assertIsNotNone(v.now())

    def test_now_time(self):
        v = SignS3View()
        self.assertIsNotNone(v.now_time())

    def test_new_uuid(self):
        v = SignS3View()
        self.assertIsNotNone(v.new_uuid())

    def test_extension_from_mimetype(self):
        v = SignS3View()
        self.assertEqual(v.extension_from_mimetype('image/jpeg'), '.jpg')
        self.assertEqual(v.extension_from_mimetype('image/png'), '.png')
        self.assertEqual(v.extension_from_mimetype('unknown'), '.obj')

    def test_get_mimetype(self):
        request = self.factory.get("/", dict(s3_object_type='hello'))
        v = SignS3View()
        self.assertEqual(v.get_mimetype(request), 'hello')

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
