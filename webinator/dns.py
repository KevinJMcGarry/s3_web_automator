import uuid

"""Classes for Route 53 Domains."""


class DomainManager:
    """Manage a Route 53 Domain."""

    def __init__(self, session):
        """Create Domain Manager Object."""
        self.session = session
        self.route53_client = self.session.client('route53')

    # getting a list of all Route53 DNS Zones in account
    def find_hosted_zone(self, domain_name):
        """Find zone matching domain_name."""
        paginator = self.route53_client.get_paginator('list_hosted_zones')
        for page in paginator.paginate():
            for zone in page['HostedZones']:
                if domain_name.endswith(zone['Name'][:-1]):  # not including final . in domain
                    return zone

        # we'll either get a zone matching our domain or None
        return None  # of no matching zone/domain_names found

    def create_hosted_zone(self, domain_name):
        """Create a hosted zone to match domain_name."""
        # Get last two elements of split list to get the zone/domain name (eg eureka software)
        zone_name = '.'.join(domain_name.split('.')[-2:]) + '.'  # be sure to end with a .
        return self.route53_client.create_hosted_zone(
            Name=zone_name,
            # unique string created by the caller
            # intended to avoid sending the same request multiple times
            CallerReference=str(uuid.uuid4())  # using uuid to generate random unique id
        )

    def create_s3_domain_record(self, zone, domain_name, endpoint):
        """Create a dns record in zone for domain_name."""
        return self.route53_client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Comment': 'Created by The Webinator',
                'Changes': [{
                        'Action': 'UPSERT',  # if it exists update, if not insert
                        'ResourceRecordSet': {
                            'Name': domain_name,
                            'Type': 'A',
                            'AliasTarget': {
                                'HostedZoneId': endpoint.dns_zone,
                                'DNSName': endpoint.host,
                                'EvaluateTargetHealth': False
                            }
                        }
                    }
                ]
            }
        )

    def create_cf_domain_record(self, zone, domain_name, cf_domain):
        """Create a dns record in zone for domain_name."""
        return self.route53_client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Comment': 'Created by The Webinator',
                'Changes': [{
                        'Action': 'UPSERT',  # if it exists update, if not insert
                        'ResourceRecordSet': {
                            'Name': domain_name,
                            'Type': 'A',
                            'AliasTarget': {
                                'HostedZoneId': 'Z2FDTNDATAQYW2',  # this id is the same for all CF distributions
                                'DNSName': cf_domain,
                                'EvaluateTargetHealth': False
                            }
                        }
                    }
                ]
            }
        )
