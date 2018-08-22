"""Classes for Cloud Front Distributions."""

import uuid
import pprint


class DistributionManager:
    """Manage CloudFront distributions."""

    def __init__(self, session):
        """Create a DistributionManager."""
        self.session = session
        self.client = self.session.client('cloudfront')

    def find_matching_dist(self, fqdn):
        """Find a CF dist matching domain_name."""
        paginator = self.client.get_paginator('list_distributions')
        for page in paginator.paginate():
            pprint.pprint(page)
            for dist in page['DistributionList'].get('Items', []):
                pprint.pprint(dist)
                exit(1)
                #for alias in dist['Aliases']['Items']:  # CF distributions can have aliases/CNAMEs assigned to them
                    #if alias == fqdn:
                        #return dist

        # return None
        return dist

    def create_dist(self, fqdn, cert):
        """Create a dist for domain_name using cert."""
        # unique id identifying origin of data (s3 bucket) to be cached in CF
        # AWS by default will append S3- to the bucket name as the unique id
        origin_id = 'S3-' + fqdn

        result = self.client.create_distribution(
            DistributionConfig={
                'CallerReference': str(uuid.uuid4()),  # generating a random uuid
                'Aliases': {
                    'Quantity': 1,
                    'Items': [fqdn]
                },
                'DefaultRootObject': 'index.html',
                'Comment': 'Created by the Webinator',
                'Enabled': True,
                # specify the bucket/s to use to get content for the CF distribution
                'Origins': {
                    'Quantity': 1,
                    # can have more than just 1 bucket as your origin
                    'Items': [{
                        'Id': origin_id,
                        'DomainName':
                        f'{fqdn}.s3.amazonaws.com',
                        'S3OriginConfig': {
                            'OriginAccessIdentity': ''
                        }
                    }]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': origin_id,
                    'ViewerProtocolPolicy': 'redirect-to-https',
                    'TrustedSigners': {
                        'Quantity': 0,
                        'Enabled': False
                    },
                    'ForwardedValues': {
                        'Cookies': {'Forward': 'all'},
                        'Headers': {'Quantity': 0},
                        'QueryString': False,
                        'QueryStringCacheKeys': {'Quantity': 0}
                    },
                    'DefaultTTL': 86400,
                    'MinTTL': 3600
                },
                'ViewerCertificate': {
                    'ACMCertificateArn': cert['CertificateArn'],
                    'SSLSupportMethod': 'sni-only',
                    'MinimumProtocolVersion': 'TLSv1.1_2016'
                }
            }
        )

        return result['Distribution']

    def await_deploy(self, dist):
        """Wait for dist to be deployed."""
        # get_waiter method is a way to programmatically wait for something to happen
        waiter = self.client.get_waiter('distribution_deployed')
        waiter.wait(Id=dist['Id'], WaiterConfig={
            'Delay': 30,  # 30 second delay
            'MaxAttempts': 50
        })