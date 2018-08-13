import boto3
from argparse import ArgumentParser

parser = ArgumentParser(description='Arguments for the S3 Boto3 Session')
parser.add_argument('Command', help='Command can be "list_buckets", "list_bucket_objects"')
parser.add_argument('--Bucket_Name', default='us', help='country zip/postal belongs to, default is "us"')

# need to add some error handling for the commands

args = parser.parse_args()

if args.Bucket_Name:  # if the Bucket_Name optional argument is used
    bucket_name = args.Bucket_Name


session = boto3.Session(profile_name='eureka-terraform')
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


if args.Command == "list_buckets":
    list_buckets()
elif args.Command == "list_bucket_objects":
    list_bucket_objects(bucket_name)


#if __name__ == '__main__':
    #list_buckets()