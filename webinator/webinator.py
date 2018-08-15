#! /usr/local/bin/python3

"""
The Webinator automates the process of deploying static websites to AWS.

- Configuring S3 buckets
  - Creates them
  - Sets them up for static website hosting
  - Deploys local files to them
- Configuring DNS with AWS Route53
- Configuring a Content Delivery Network (CDN) with SSL using AWS CloudFront
"""

from argparse import ArgumentParser
from pathlib import Path
import mimetypes  # for deciphering the mimetype of files
import boto3
from botocore.exceptions import ClientError  # for catching Boto3 specific errors

parser = ArgumentParser(description='Arguments for the S3 Boto3 Session')
parser.add_argument('Command', help='Command can be "list_buckets", "list_bucket_objects", '
                                    '"setup_bucket", "sync_s3"')
parser.add_argument('Region', help='Specify the AWS Region you are working in eg us-west-2')
parser.add_argument('--Bucket_Name', help='Type in the name of an S3 bucket')
parser.add_argument('--Website_Root', help='Type in the full path to the website files that you want to sync '
                                           '(without quotes)')

# need to add some error handling for the commands

args = parser.parse_args()

if args.Bucket_Name:
    bucket_name = args.Bucket_Name
if args.Region:
    aws_region = args.Region
if args.Website_Root:
    website_root_path = args.Website_Root

# Setting Boto3 session and creating s3 resource object
session = boto3.Session(profile_name='eureka-terraform', region_name='us-west-2')
s3 = session.resource('s3')


def list_buckets():
    """List all S3 Buckets."""
    for bucket in s3.buckets.all():
        print(bucket)


def list_bucket_objects(bucket):
    """List Objects in an S3 Bucket."""
    print(f"Objects in Bucket {bucket}")
    print("-" * 35)
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)


def setup_bucket(bucket):
    """Create and configure an S3 Bucket."""
    try:
        s3_bucket = s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={'LocationConstraint': aws_region})
    except ClientError as err:
        if err.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
            # if bucket already exists, continue with the application without creating a bucket
            # with s3_bucket being assigned the name passed in via the argument
        else:
            raise err  # raise any other error found that isn't 'BucketAlreadyOwnedByYou'

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
    """ % s3_bucket.name

    # strip off \n characters at beginning and end of policy so that it is valid
    s3_bucket_website_policy = s3_bucket_website_policy.strip()

    pol = s3_bucket.Policy()  # create s3 policy object
    pol.put(Policy=s3_bucket_website_policy)  # upload policy to s3 bucket

    # website configuration
    ws = s3_bucket.Website()
    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }
    })


def sync(path_name, bucket_name):
    """Sync contents of PATHNAME to S3 Bucket."""
    s3_bucket_name = bucket_name
    print(f"name of bucket is {s3_bucket_name}")

    # creating a Path object from the user's cli website path argument
    # the expanduser() method is for expanding ~ to the actual user's homedir
    # the resolve() method resolve symlinks and eliminate “..” components
    website_root_path = Path(path_name).expanduser().resolve()

    handle_directory(website_root_path, s3_bucket_name)


def handle_directory(source_dir, s3_bucket_name):
    """Identify website files and folders that will be uploaded to S3."""
    for item in source_dir.iterdir():
        if item.is_dir():
            handle_directory(item, s3_bucket_name)  # if item is a directory, use that dir as input int the same function (recursion)
        if item.is_file():
            if item.match('.DS_Store'):  # skip mac index files
                continue
            print(f"Path: {item}\n Key: {item.relative_to(website_root_path)}")
            upload_file(s3_bucket_name, str(item), str(item.relative_to(website_root_path)))
            # path is the full path to the file and the key is the part we upload to s3 - the relative path to the file


def upload_file(s3_bucket, path, key):
    """Upload website files to specified S3 bucket."""
    s3_bucket = s3.Bucket(bucket_name)  # creating an S3 object to work with S3 buckets

    # guess_type method gives us a tuple, the first element is the file
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'  # if can't guess type, assign text/plain mimetype

    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': content_type
        }
    )


if args.Command == "list_buckets":
    list_buckets()
elif args.Command == "list_bucket_objects":
    list_bucket_objects(bucket_name)
elif args.Command == "setup_bucket":
    setup_bucket(bucket_name)
elif args.Command == "sync_s3":
    sync(website_root_path, bucket_name)
else:
    print("Please enter a valid command")

if __name__ == '__main__':
    list_buckets()
