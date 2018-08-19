# AWS Automation - S3_Web_Automator

## S3 Webinator
This script will sync a local directory to an S3 bucket, and optionally configure Route53 and CloudFront as well.

### Features
The S3 Webinator currently has the following features:

- List Buckets
- List Contents of a Bucket
- Create an S3 bucket and configure it as a website
- Sync website directory tree to S3 bucket
- Set AWS profile with --AWS_Profile=<profileName>
- Configure Route53 Zone and Records

example - python webinator.py list\_bucket\_objects us-west-2 --AWS_Profile=someProfile --Bucket_Name someS3Bucket

