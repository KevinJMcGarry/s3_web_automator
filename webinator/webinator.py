import boto3
from argparse import ArgumentParser
from botocore.exceptions import ClientError  # catching Boto3 specific errors


parser = ArgumentParser(description='Arguments for the S3 Boto3 Session')
parser.add_argument('Command', help='Command can be "list_buckets", "list_bucket_objects", "setup_bucket"')
parser.add_argument('Region', help='Specify the AWS Region you are working in eg us-west-2')
parser.add_argument('--Bucket_Name', help='Type in the name of an S3 bucket')

# need to add some error handling for the commands

args = parser.parse_args()

if args.Bucket_Name:  # if the Bucket_Name optional argument is used
    bucket_name = args.Bucket_Name
if args.Region:
    aws_region = args.Region


session = boto3.Session(profile_name='eureka-terraform', region_name='us-west-2')
s3 = session.resource('s3')

def list_buckets():
    """List all S3 Buckets"""
    for bucket in s3.buckets.all():
        print(bucket)


def list_bucket_objects(bucket):
    """List Objects in an S3 Bucket"""
    print(f"Objects in Bucket {bucket}")
    print("-" * 35)
    for obj in s3.Bucket(bucket).objects.all():
        print(obj)


def setup_bucket(bucket):
    """Create and configure an S3 Bucket"""
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

    return


if args.Command == "list_buckets":
    list_buckets()
elif args.Command == "list_bucket_objects":
    list_bucket_objects(bucket_name)
elif args.Command == "setup_bucket":
    setup_bucket(bucket_name)


#if __name__ == '__main__':
    #list_buckets()