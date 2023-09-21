(function() {

    window.S3Upload = (function() {

        S3Upload.prototype.s3_object_name = 'default_name';

        S3Upload.prototype.s3_sign_put_url = '/signS3put';

        S3Upload.prototype.file_dom_el = null;

        S3Upload.prototype.file_dom_selector = '#file_upload';

        S3Upload.prototype.x_amz_acl = 'public-read';

        S3Upload.prototype.onFinishS3Put = function(public_url, private_url) {
            return console.log('base.onFinishS3Put()', public_url, private_url);
        };

        S3Upload.prototype.onProgress = function(percent, status) {
            return console.log('base.onProgress()', percent, status);
        };

        S3Upload.prototype.onError = function(status) {
            return console.log('base.onError()', status);
        };

        function S3Upload(options) {
            if (options === null) options = {};
            let option;
            for (option in options) {
                this[option] = options[option];
            }
            this.handleFileSelect(
                this.file_dom_el ||
                    document.querySelector(this.file_dom_selector)
            );
        }

        S3Upload.prototype.getXMLError = function(xmlDoc) {
            if (xmlDoc.getElementsByTagName('Message').length > 0) {
                return xmlDoc.getElementsByTagName('Message')[0].textContent;
            }
            return null;
        }

        S3Upload.prototype.handleFileSelect = function(file_element) {
            var f, files, _i, _len, _results;

            files = file_element.files;

            if (files.length === 0) {
                return;
            }

            _results = [];

            this.onProgress(0, 'Upload started.');

            for (_i = 0, _len = files.length; _i < _len; _i++) {
                f = files[_i];
                _results.push(this.uploadFile(f));
            }

            return _results;
        };

        S3Upload.prototype.createCORSRequest = function(method, url) {
            var xhr;
            xhr = new XMLHttpRequest();

            if (xhr.withCredentials !== null) {
                xhr.open(method, url, true);
            } else if (typeof XDomainRequest !== "undefined") {
                xhr = new XDomainRequest();
                xhr.open(method, url);
            } else {
                xhr = null;
            }

            return xhr;
        };

        S3Upload.prototype.executeOnSignedUrl = function(file, callback) {
            var this_s3upload, xhr;
            this_s3upload = this;
            xhr = new XMLHttpRequest();
            xhr.open('GET', this.s3_sign_put_url +
                     '?s3_object_type=' + file.type +
                     '&s3_object_name=' + this.s3_object_name, true);
            xhr.overrideMimeType('text/plain; charset=x-user-defined');
            xhr.onreadystatechange = function() {
                var result;
                if (this.readyState === 4 && this.status === 200) {
                    try {
                        result = JSON.parse(this.responseText);
                    } catch (error) {
                        this_s3upload.onError('Signing server returned some ugly/empty JSON: "' + this.responseText + '"');
                        return false;
                    }

                    let signedGetUrl = null;
                    if (result.presigned_get_url) {
                        signedGetUrl = decodeURIComponent(
                            result.presigned_get_url);
                    }

                    return callback(
                        result.presigned_post_url,
                        result.url,
                        signedGetUrl
                    );
                } else if (this.readyState === 4 && this.status !== 200) {
                    return this_s3upload.onError('Could not contact request signing server. Status = ' + this.status);
                }
            };
            return xhr.send();
        };

        S3Upload.prototype.uploadToS3 = function(
            file, urlObj, public_url, presigned_get_url
        ) {
            var this_s3upload, xhr;
            this_s3upload = this;

            xhr = this.createCORSRequest('POST', urlObj.url);

            if (!xhr) {
                this.onError('CORS not supported');
            } else {
                xhr.onload = function() {
                    if (xhr.status === 200 || xhr.status === 204) {
                        this_s3upload.onProgress(100, 'Upload completed.');
                        return this_s3upload.onFinishS3Put(
                            public_url, presigned_get_url
                        );
                    } else {
                        let parser = new DOMParser();
                        let xmlDoc = parser.parseFromString(
                            xhr.responseText, xhr.responseXML.contentType);

                        let xmlError = this_s3upload.getXMLError(xmlDoc);

                        let errText = xhr.status;
                        if (xmlError) {
                            errText = xmlError;
                        }

                        return this_s3upload.onError(
                            'Upload error: ' + errText);
                    }
                };
                xhr.onerror = function() {
                    return this_s3upload.onError('Upload failed.');

                };
                xhr.upload.onprogress = function(e) {
                    var percentLoaded;
                    if (e.lengthComputable) {
                        percentLoaded = Math.round((e.loaded / e.total) * 100);
                        return this_s3upload.onProgress(percentLoaded, percentLoaded === 100 ? 'Finalizing.' : 'Uploading.');
                    }
                };
            }

            const formData = new FormData();

            Object.keys(urlObj.fields).forEach((key) => {
                formData.append(key, urlObj.fields[key]);
            });

            formData.append('file', file);

            if (this.x_amz_acl) {
                xhr.setRequestHeader('x-amz-acl', this.x_amz_acl);
            }

            return xhr.send(formData);
        };

        S3Upload.prototype.uploadFile = function(file) {
            var this_s3upload;
            this_s3upload = this;
            return this.executeOnSignedUrl(
                file, function(signedURL, publicURL, signedGetURL) {
                    return this_s3upload.uploadToS3(
                        file, signedURL, publicURL, signedGetURL
                    );
                });
        };

        return S3Upload;

    })();

}).call(this);
