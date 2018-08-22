import pprint

"""Classes for ACM Certificates."""

class CertificateManager:
    """Create a CertificateManager."""
    def __init__(self, session):
        self.session = session
        self.client = self.session.client('acm', region_name='us-east-1')

    # method to pull out all the Subject Alternative Names/Child/Sub Domains assigned to certificate
    def cert_matches(self, cert_arn, domain_name):
        """Return True if cert matches domain_name."""
        cert_details = self.client.describe_certificate(CertificateArn=cert_arn)
        alt_names = cert_details['Certificate']['SubjectAlternativeNames']
        for name in alt_names:
            if name == domain_name:  # if the SAN exactly matches the domain name
                return True
            if name[0] == '*' and domain_name.endswith(name[1:]):
                return True
        return False

    def find_matching_cert(self, domain_name):
        """Find a certificate matching domain_name."""
        paginator = self.client.get_paginator('list_certificates')
        for page in paginator.paginate(CertificateStatuses=['ISSUED']):  # only search for certs that have been issued
            for cert in page['CertificateSummaryList']:
                print(cert)
                if self.cert_matches(cert['CertificateArn'], domain_name):
                    return cert

        return None  # No matching cert found in the loops above

