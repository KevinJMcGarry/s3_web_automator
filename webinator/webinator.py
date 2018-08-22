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

import boto3
import pprint
import util


# This file uses BucketManager for most of its logic
from bucket import BucketManager
from dns import DomainManager
from certificate import CertificateManager
from cdn import DistributionManager


parser = ArgumentParser(description='Arguments for the S3 Boto3 Session')
parser.add_argument('Command', help='Command can be: "list_buckets", "list_bucket_objects", '
                                    '"setup_bucket", "sync_s3", "setup_domain", "find_cert", "setup_cdn"')
parser.add_argument('Region', help='Specify the AWS Region you are working in eg us-west-2')
parser.add_argument('--Bucket_Name', help='Type in the name of an S3 bucket')
parser.add_argument('--Website_Root', help='Type in the full path to the website files that you want to sync '
                                           '(without quotes)')
parser.add_argument('--AWS_Profile', help='Type in the AWS Profile you wish to use for this session')
parser.add_argument('--Site_DNS', help="Type in the FQDN for the hosted site."
                                       "This should match your bucket name.")
parser.add_argument('--Domain', help="Type in the Domain Name for your site. eg eureka.software")

# need to add some error handling for the above commands

args = parser.parse_args()

if args.Bucket_Name:
    bucket_name = args.Bucket_Name
if args.Region:
    aws_region = args.Region
if args.Website_Root:
    website_root_path = args.Website_Root
if args.AWS_Profile:
    aws_profile = args.AWS_Profile
if args.Site_DNS:
    site_dns = args.Site_DNS
if args.Domain:
    domain_name = args.Domain


# Setting Boto3 session and creating s3 resource object
# programmatically authenticate to AWS via boto3
session = boto3.Session(profile_name=aws_profile, region_name='us-west-2')

# S3 and Route53 session objects using respective classes
bucket_manager = BucketManager(session)  # creating an S3 bucket_manager object from BucketManager class
domain_manager = DomainManager(session)  # creating a route53 domain_manager object
cert_manager = CertificateManager(session)  # creating a certificate manager object
dist_manager = DistributionManager(session)

def list_buckets():
    """List all S3 Buckets."""
    for bucket in bucket_manager.all_buckets():  # calling the all_buckets method
        print(bucket)


def list_bucket_objects(bucket):
    """List Objects in an S3 Bucket."""
    print(f"Objects in Bucket {bucket}")
    print("-" * 45)
    for obj in bucket_manager.all_objects(bucket):
        print(obj)


def setup_bucket(bucket):
    """Create and configure an S3 Bucket."""
    s3_bucket = bucket_manager.initialize_bucket(bucket, aws_region)
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.configure_website(s3_bucket)


def sync(path_name, bucket):
    """Sync contents of PATHNAME to S3 Bucket."""
    bucket_manager.sync(path_name, bucket)
    print(bucket_manager.get_bucket_url(bucket_manager.s3.Bucket(bucket_name)))


def setup_domain(fqdn):
    """Configure Domain to point to Bucket."""
    # zone is the Route53 zone we find or the one we create if it doesn't exist
    # reminder, for s3 bucket websites, the fqdn and the bucket must be the same name
    bucket = bucket_manager.get_bucket(fqdn)

    zone = domain_manager.find_hosted_zone(fqdn) \
        or domain_manager.create_hosted_zone(fqdn)
    endpoint = util.get_endpoint(bucket_manager.get_region_name(bucket))

    a_record = domain_manager.create_s3_domain_record(zone, fqdn, endpoint)
    print(f"Domain configured http://{fqdn}")
    print(f"A Record is {a_record}")


def find_cert(domain):
    """Find a certificate for the supplied domain."""
    pprint.pprint(cert_manager.find_matching_cert(domain))


def setup_cdn(fqdn, domain_name):
    """Set up CloudFront CDN for the specified domain pointing to specified bucket."""
    # searching to see if we already have a CF Distribution setup for this domain
    dist = dist_manager.find_matching_dist(fqdn)

    # if we don't find a CF distribution for this domain, create it
    if not dist:
        cert = cert_manager.find_matching_cert(fqdn)
        if not cert:  # SSL is not optional at this time
            print("Error: No matching cert found.")
            return

        # create a CF distribution
        dist = dist_manager.create_dist(fqdn, cert)
        print("Waiting for distribution deployment...")
        dist_manager.await_deploy(dist)

    # create route53 record for the CF distribution
    zone = domain_manager.find_hosted_zone(domain_name) \
        or domain_manager.create_hosted_zone(domain_name)

    domain_manager.create_cf_domain_record(zone, fqdn, dist['DomainName'])
    print(f"Domain configured: https://{fqdn}")

    return


if args.Command == "list_buckets":
    list_buckets()
elif args.Command == "list_bucket_objects":
    list_bucket_objects(bucket_name)
elif args.Command == "setup_bucket":
    setup_bucket(bucket_name)
elif args.Command == "sync_s3":
    sync(website_root_path, bucket_name)
elif args.Command == "setup_domain":
    setup_domain(site_dns)
elif args.Command == "find_cert":
    find_cert(domain_name)
elif args.Command == "setup_cdn":
    setup_cdn(site_dns, domain_name)
else:
    print("Please enter a valid command")

if __name__ == '__main__':
    print("... Output obtained using the Webinator! ...")
