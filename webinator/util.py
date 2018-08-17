"""Utilities for webinator."""

# This utility is used for getting the endpoint/website url of the s3 bucket
# Since the Website Endpoint format isn't the same for each region, we place all the data from this site into
# code - https://docs.aws.amazon.com/general/latest/gr/rande.html#s3_website_region_endpoints

# using a namedtuple for the data structure. It is a cross between a tuple and a named object.
# Each item is immutable like a tuple, but you can access the elements by name like an object or dictionary
# (instead of using something like endpoint[0] for the region or endpoint[1] for the host/url etc.
# you can do something like ep1.region_name or ep1.dns_zone after creating the ep1 object
# ep1 = Endpoint('US East (Ohio)', 's3-website.us-east-2.amazonaws.com', 'Z2O1EMRO9K5GLX')

from collections import namedtuple

Endpoint = namedtuple('Endpoint', ['region_name', 'host', 'dns_zone'])

# dictionary that implements a map of region to endpoints
# used to create endpoint objects (eg ep1, ep2 etc.)
region_to_endpoint = {
    'us-east-2': Endpoint('US East (Ohio)', 's3-website.us-east-2.amazonaws.com', 'Z2O1EMRO9K5GLX'),
    'us-east-1': Endpoint('US East (N. Virginia)', 's3-website-us-east-1.amazonaws.com', 'Z3AQBSTGFYJSTF'),
    'us-west-1': Endpoint('US West (N. California)', 's3-website-us-west-1.amazonaws.com', 'Z2F56UZL2M1ACD'),
    'us-west-2': Endpoint('US West (Oregon)', 's3-website-us-west-2.amazonaws.com', 'Z3BJ6K6RIION7M'),
    'ca-central-1': Endpoint('Canada (Central)', 's3-website.ca-central-1.amazonaws.com', 'Z1QDHH18159H29'),
    'ap-south-1': Endpoint('Asia Pacific (Mumbai)', 's3-website.ap-south-1.amazonaws.com', 'Z11RGJOFQNVJUP'),
    'ap-northeast-2': Endpoint('Asia Pacific (Seoul)', 's3-website.ap-northeast-2.amazonaws.com', 'Z3W03O7B5YMIYP'),
    'ap-northeast-3': Endpoint('Asia Pacific (Osaka-Local)', 's3-website.ap-northeast-3.amazonaws.com', 'Z2YQB5RD63NC85'),
    'ap-southeast-1': Endpoint('Asia Pacific (Singapore)', 's3-website-ap-southeast-1.amazonaws.com', 'Z3O0J2DXBE1FTB'),
    'ap-southeast-2': Endpoint('Asia Pacific (Sydney)', 's3-website-ap-southeast-2.amazonaws.com', 'Z1WCIGYICN2BYD'),
    'ap-northeast-1': Endpoint('Asia Pacific (Tokyo)', 's3-website-ap-northeast-1.amazonaws.com', 'Z2M4EHUR26P7ZW'),
    'cn-northwest-1': Endpoint('China (Ningxia)', 's3-website.cn-northwest-1.amazonaws.com.cn', None),
    'eu-central-1': Endpoint('EU (Frankfurt)', 's3-website.eu-central-1.amazonaws.com', 'Z21DNDUVLTQW6Q'),
    'eu-west-1': Endpoint('EU (Ireland)', 's3-website-eu-west-1.amazonaws.com', 'Z1BKCTXD74EZPE'),
    'eu-west-2': Endpoint('EU (London)', 's3-website.eu-west-2.amazonaws.com', 'Z3GKZC51ZF0DB4'),
    'eu-west-3': Endpoint('EU (Paris)', 's3-website.eu-west-3.amazonaws.com', 'Z3R1K369G5AVDG'),
    'sa-east-1': Endpoint('South America (São Paulo)', 's3-website-sa-east-1.amazonaws.com', 'Z7KQH4QJS55SO'),
}

# two helper functions to make use of the data structure above


def known_region(region_name):  # Determine if region exists. Return True if region_name is in map
    """Return true if this is a known region."""
    return region_name in region_to_endpoint


def get_endpoint(region_name):
    """Get the s3 website hosting endpoint for this region."""
    return region_to_endpoint[region_name]
