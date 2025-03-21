[![Build Status](https://travis-ci.org/ccnmtl/django-s3sign.svg?branch=master)](https://travis-ci.org/ccnmtl/django-s3sign)
[![Coverage Status](https://coveralls.io/repos/github/ccnmtl/django-s3sign/badge.svg?branch=master)](https://coveralls.io/github/ccnmtl/django-s3sign?branch=master)

# django-s3sign
s3 sign view for django

## installation

    $ pip install django-s3sign

## usage

Add `s3sign` to `INSTALLED_APPS`. Subclass `s3sign.views.SignS3View`
and override as needed.

Attributes you can override (and their default values):

```
    name_field = 's3_object_name'
    type_field = 's3_object_type'
    expiration_time = 10
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
    acl = "public-read"
```

Methods you can override:

* `get_aws_access_key(self)`
* `get_aws_secret_key(self)`
* `get_bucket(self)`
* `get_mimetype(self, request)`
* `extension_from_mimetype(self, mime_type)`
* `now()` # useful for unit tests
* `now_time()` # useful for unit tests
* `basename()`
* `get_object_name(self, extension)`

Most of those should be clear. Read the source if in doubt.


Eg to use a different root path:


```
from s3sign.views import SignS3View
...

class MySignS3View(LoggedInView, SignS3View):
    root = 'uploads/'
```

With a different S3 bucket:

```
class MySignS3View(LoggedInView, SignS3View):
    def get_bucket(self):
        return settings.DIFFERENT_BUCKET_NAME
```

Keeping the uploaded filename instead of doing a random one and
whitelisted extension:

```
class MySignS3View(LoggedInView, SignS3View):
    def basename(self, request):
        filename = request.GET[self.get_name_field()]
        return os.path.basename(filename)

    def extension(self, request):
        filename = request.GET[self.get_name_field()]
        return os.path.splitext(filename)[1]
```


### javascript/forms

The required javascript is also included, so you can include it in
your page with:

    {% load static %}

    <script src="{% static 's3sign/js/s3upload.js' %}"></script>

Your form would then somewhere have a bit like:

    <form method="post">
        <p id="status">
            <strong>Please select a file</strong>
        </p>

        <input type="hidden" name="s3_url" id="uploaded-url" />
        <input type="file" id="file" onchange="s3_upload();"/>
    </form>

And

```
<script>
function s3_upload() {
    var s3upload = new S3Upload({
        file_dom_el: null, // Optional, and overrides file_dom_selector
                           // when present.
        file_dom_selector: '#file',
        s3_sign_put_url: '/sign_s3/', // change this if you route differently
        s3_object_name: $('#file')[0].value,

        onProgress: function(percent, message) {
            $('#status').text('Upload progress: ' + percent + '% ' + message);
        },
        onFinishS3Put: function(url) {
            $('#uploaded-url').val(url);
        },
        onError: function(status) {
            $('#status').text('Upload error: ' + status);
        }
    });
}
</script>
```
