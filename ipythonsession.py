# coding: utf-8
import boto3
session = boto3.Session(profile_name='eureka-terraform')
s3 = session.resource('s3')

bucket_name = s3.create_bucket(Bucket='automatingaws-kevin-newbucket', CreateBucketConfiguration={'LocationConstraint': 'us-west-2'})
# for Location.Constraint, should be able to use session.region_name. This is pulled from the aws cli config file for
# the profile specified

