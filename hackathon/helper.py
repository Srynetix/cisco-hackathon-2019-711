from meraki_sdk.meraki_sdk_client import MerakiSdkClient
from . import config


from meraki_sdk.meraki_sdk_client import MerakiSdkClient


def check_if_existing_organization(organization_id):
    client = MerakiSdkClient(config.X_CISCO_MERAKI_API_KEY)
    orgs = client.organizations.get_organizations()
    for org in orgs:
        if organization_id == org['id']:
            return True
    return False


def check_if_network_id_in_organization(organizationDict)
    client = MerakiSdkClient(config.X_CISCO_MERAKI_API_KEY)
    if organizationDict:
        networks = client.networks.get_organization_networks(organizationDict)
        if networks:
            return True

    return False
