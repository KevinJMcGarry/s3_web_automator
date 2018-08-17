"""Classes for S3 Buckets.

Encapsulation of our bucket logic in this module
"""

import mimetypes
from pathlib import Path

import boto3
from botocore.exceptions import ClientError  # for catching Boto3 specific errors

from functools import reduce
from hashlib import md5
import util

class BucketManager:
    """Manage an S3 Bucket."""

    # setting a class attribute for the chunk size of s3 files to be uploaded
    # if a file is larger than this size, it will be broken into chunks <= 8388608 bytes
    # this chunk size comes from the AWS s3 documentation
    # must take chunk size into consideration as files that have been chunked received different etags
    # than the hash of the full file that we are going to upload
    CHUNK_SIZE = 8388608

    def __init__(self, session):  # instances of this class will be constructed with this function
        """Create a BucketManager Object."""
        self.session = session
        self.s3 = self.session.resource('s3')

        # create transfer config object to be used each time we upload a file
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize=self.CHUNK_SIZE,
            multipart_threshold=self.CHUNK_SIZE
        )

        # empty manifest object to be used by load_manifest method below, used for getting s3 bucket e-tags
        self.manifest = {}

    def get_region_name(self, bucket):
        """Get the bucket's region name."""
        # creating location object to get location information about the bucket
        bucket_location = self.s3.meta.client.get_bucket_location(Bucket=bucket.name)

        return bucket_location["LocationConstraint"] or 'us-east-1'
        # strange AWS API behavior, all regions are determined using the bucket_location object unless
        # us-east-1, this region has to be specified

    def get_bucket_url(self, bucket):
        """Get the website URL for this bucket."""
        return f"http://{bucket.name}.{util.get_endpoint(self.get_region_name(bucket)).host}"

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

    def load_manifest(self, bucket):
        """Load manifest for s3 bucket caching purposes."""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        # using pagination to load data by pages into memory rather than the entire data set all at once
        for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents', []):  # empty list covers empty pages being returned
                self.manifest[obj['Key']] = obj['ETag']  # populating manifest with ETags for each s3 object

        # before we upload our files, we want to load our files from the manifest first

    @staticmethod
    def hash_data(data):
        """Get hash value for data files to be uploaded to S3."""
        hash = md5()
        hash.update(data)

        return hash

    def gen_etag(self, path):
        """Generate etag for file."""
        print("generating hashes for local files")
        # creating a list of hashes for our file to upload.
        # The list if for the scenario where multiple hashes are created
        # (eg the file is so large that is is chunked - split into multiple parts before being uploaded)
        hashes = []

        with open(path, 'rb') as file:
            while True:  # used to iterate over the chunks of the file
                data = file.read(self.CHUNK_SIZE)  # read in the file data into memory up to the defined chunk_size

                if not data:
                    break  # break out of loop if no more data is available to be read

                hashes.append(self.hash_data(data))  # append to hashes list

        if not hashes:  # if no hashes were generated (eg the file was empty)
            print("no hashes generated")
            return
        elif len(hashes) == 1:  # if just one hash returned (eg the file was less than the chunk size)
            print("one hash generated")
            return f"{hashes[0].hexdigest()}"
        else:
            hash = self.hash_data(reduce(lambda x, y: x + y, (h.digest() for h in hashes)))
            # basically this is the algorithm AWS uses to generate etags
            # first part takes a hash,
            # the reduce function takes another function (in this case a lambda/anonymous function)
            # lambda function takes two arguments
            # reduce will take a list of things, iterate over it and append each element to the previous one
            # each element will be the digest
            # (h.digest() for h in hashes))) == getting a digest for each of the hashes
            # x + y == appending those digests together
            print("multiple hashes generated")
            return f'"{hash.hexdigest()}"-{len(hashes)}'


        # the way AWS works is that it takes a hash of each chunk of the data
        # and then takes a hash of those hashes - this becomes the etag of the file
        # note the etag uses a double quote. So the etag string also includes double quotes in the string
        # this is the reason we include he double quotes inside the f string

    def upload_file(self, bucket, path, key):
        """Upload website files to specified S3 bucket."""
        # guess_type method gives us a tuple, the first element is the file
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'  # if can't guess type, assign text/plain mimetype

        # generate an etag for a particular file
        etag = self.gen_etag(path)

        # the manifest are the etags from AWS
        # conditional checks to see if the digest of our local file matches the etag of the file in s3
        # if it does, just return (files are the same), if not, run the upload.file method
        if self.manifest.get(key, '') == etag:  # if key doesn't exist, we'll get an empty string
            print(f"Skipping {key}, etags match")
            return

        # return statement isn't required but can be used as a design decision
        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            },
            Config=self.transfer_config
        )

    def sync(self, path_name, bucket_name):
        """Sync contents of path_name to bucket."""
        bucket = self.s3.Bucket(bucket_name)
        self.load_manifest(bucket)

        website_root_path = Path(path_name).expanduser().resolve()

        # creating a Path object from the user's cli website path argument
        # the expanduser() method is for expanding ~ to the actual user's homedir
        # the resolve() method resolve symlinks and eliminate “..” components

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
