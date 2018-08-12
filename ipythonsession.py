# coding: utf-8
import boto3
session = boto3.Session(profile_name='eureka-terraform')
s3 = session.resource('s3')
