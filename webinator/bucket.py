"""Classes for S3 Buckets.
Encapsulation of our bucket logic in this module"""

import mimetypes
from pathlib import Path

from botocore.exceptions import ClientError  # for catching Boto3 specific errors


class BucketManager:
    """Manage an S3 Bucket."""

    def __init__(self, session):  # instances of this class will be constructed with this function
        """Create a BucketManager Object."""
        self.session = session
        self.s3 = self.session.resource('s3')

    def all_buckets(self):
        """Get all S3 Buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Get all objects in an S3 Bucket."""
        return self.s3.Bucket(bucket_name).objects.all()

    def initialize_bucket(self, bucket_name, aws_region):
        """Create new S3 bucket or return existing one by name."""
        try:  # trying to create the bucket
            s3_bucket = self.s3.create_bucket(Bucket=bucket_name,
                                              CreateBucketConfiguration={'LocationConstraint': aws_region})
        except ClientError as err:
            if err.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
                # if bucket already exists, continue with the application without creating a bucket
                # with s3_bucket being assigned the name passed in via the argument
            else:
                raise err  # raise any other error found that isn't 'BucketAlreadyOwnedByYou'

        return s3_bucket

    def set_policy(self, bucket):
        """Set S3 Bucket Policy to be readable by everyone."""
        s3_bucket_website_policy = """
        {
          "Version":"2012-10-17",
          "Statement":[{
          "Sid":"PublicReadGetObject",
          "Effect":"Allow",
          "Principal": "*",
              "Action":["s3:GetObject"],
              "Resource":["arn:aws:s3:::%s/*"
              ]
            }
          ]
        }
        """ % bucket.name

        # strip off \n characters at beginning and end of policy so that it is valid
        s3_bucket_website_policy = s3_bucket_website_policy.strip()

        pol = bucket.Policy()  # create s3 policy object
        pol.put(Policy=s3_bucket_website_policy)  # upload policy to s3 bucket

    def configure_website(self, bucket):
        """Configure Website Default documents."""
        # website configuration
        ws = bucket.Website()
        ws.put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }
        })

    @staticmethod  # this method is static as it doesn't rely on BucketManager class at all
    def upload_file(bucket, path, key):
        """Upload website files to specified S3 bucket."""

        # guess_type method gives us a tuple, the first element is the file
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'  # if can't guess type, assign text/plain mimetype

        # return statement isn't required but can be used as a design decision
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            }
        )

    def sync(self, path_name, bucket_name):
        """Sync contents of path_name to bucket."""
        bucket = self.s3.Bucket(bucket_name)
        website_root_path = Path(path_name).expanduser().resolve()

        def handle_directory(source_dir):
            """Identify and upload website files and folders to S3."""
            for item in source_dir.iterdir():
                if item.is_dir():
                    handle_directory(item)  # if item is a directory, use that
                                            # dir as input int the same function (recursion)
                if item.is_file():
                    if item.match('.DS_Store'):  # skip mac index files
                        continue
                    print(f"Path: {item}\n Key: {item.relative_to(website_root_path)}")
                    self.upload_file(bucket, str(item), str(item.relative_to(website_root_path)))
                    # calling upload_file method above
                    # path is the full path to the file and the key is the part we upload to s3
                    #  - the relative path to the file

        handle_directory(website_root_path)
