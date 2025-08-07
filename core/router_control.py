# wifi_hotspot/core/router_control.py

import logging

logger = logging.getLogger(__name__)

def create_router_user(company, token: str, mac_address: str, ip_address: str):
    """
    Simulates creating a new user on the Savanna router, including their IP address.
    """
    logger.info(f"Simulating: Creating a router user for company '{company.name}' with MAC '{mac_address}' and IP '{ip_address}' for token '{token}'.")
    # Placeholder logic - always succeeds for now
    return True, "Simulated user creation successful."

def enable_router_user(company, token: str, mac_address: str, ip_address: str):
    """
    Simulates enabling a user on the Savanna router.
    """
    logger.info(f"Simulating: Enabling router user for company '{company.name}' with MAC '{mac_address}' and IP '{ip_address}' for token '{token}'.")
    # Placeholder logic - always succeeds for now
    return True, "Simulated user enabled successfully."

def block_mac_on_router(mac_address: str, company):
    """
    Simulates blocking a MAC address on the Savanna router.
    """
    logger.info(f"Simulating: Blocking MAC address '{mac_address}' on router for company '{company.name}'.")
    # Placeholder logic - always succeeds for now
    return True, "Simulated MAC block successful."
