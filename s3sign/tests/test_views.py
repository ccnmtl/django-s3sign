from django.test import TestCase, RequestFactory
from s3sign.views import SignS3View


class TestView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_now(self):
        v = SignS3View()
        self.assertIsNotNone(v.now())
