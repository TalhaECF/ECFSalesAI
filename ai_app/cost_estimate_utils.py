import requests


def fetch_azure_pricing(service_name, sku_name, region="East US", tier="", price_type="Consumption"):
    """
    Fetches Azure pricing data for a specific service and SKU in a given region.
    Uses exact equality operators and formats the region properly.

    :param service_name: e.g. "Virtual Machines" or "App Service"
    :param sku_name: e.g. "Standard_D2s_v3" or "B1"
    :param region: Region as displayed by the user (will be normalized, e.g. "East US" → "eastus")
    :param tier: Optional extra filter (used as an equality check on productName)
    :param price_type: Filter by price type (default "Consumption"; other options include "Reservation")
    :return: The lowest retailPrice found or None if not found.
    """
    # Format region to match API (e.g. "East US" → "eastus")
    region_formatted = region.replace(" ", "").lower()
    base_url = "https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview"

    # Build filter query using equality operators.
    filter_parts = [
        f"serviceName eq '{service_name}'",
        f"armRegionName eq '{region_formatted}'",
        f"skuName eq '{sku_name}'",
        f"priceType eq '{price_type}'"
    ]
    if tier:
        filter_parts.append(f"productName eq '{tier}'")
    filter_query = " and ".join(filter_parts)
    params = {"$filter": filter_query}

    all_prices = []
    url = base_url
    while url:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch pricing for {service_name}: {response.status_code}")
        data = response.json()
        all_prices.extend(data.get("Items", []))
        url = data.get("NextPageLink")
        # For subsequent pages, parameters have been included already in the NextPageLink URL.
        params = {}

    if not all_prices:
        print(f"No pricing data found for {service_name} ({sku_name}) in {region_formatted}.")
        debug_service_pricing(service_name, region_formatted)
        return None

    # Return the lowest retailPrice found (you could change this strategy as needed)
    best_item = min(all_prices, key=lambda item: item.get("retailPrice", float('inf')))
    return best_item["retailPrice"]


def debug_service_pricing(service_name, region="eastus"):
    """
    Prints available pricing info for a given service and region to help determine
    valid skuName/productName values.
    """
    base_url = "https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview"
    filter_query = f"serviceName eq '{service_name}' and armRegionName eq '{region}'"
    params = {"$filter": filter_query}

    response = requests.get(base_url, params=params)
    if response.status_code != 200:
        print(f"Failed to fetch debug pricing: {response.status_code}")
        return
    data = response.json()
    # for item in data.get("Items", []):
    #     print(f"Service: {item['serviceName']}, SKU: {item['skuName']}, Product: {item['productName']}")


def get_azure_service_cost(services, region="East US", hours_per_month=730, price_type="Consumption"):
    """
    Fetches the estimated monthly cost for a list of Azure services.
    Now includes SKU Name and Region in the breakdown.

    :param services: List of dicts e.g. [{"serviceName": "Virtual Machines", "skuName": "Standard_D2s_v3"}, ...]
    :param region: Region (will be normalized)
    :param hours_per_month: Usage hours per month
    :param price_type: Pricing type filter (e.g. "Consumption")
    :return: A dict with overall total cost and a detailed breakdown.
    """
    total_cost = 0
    cost_breakdown = {}

    for service in services:
        s_name = service.get("serviceName")
        sku = service.get("skuName")
        tier = service.get("tier", "")

        price = fetch_azure_pricing(s_name, sku, region, tier, price_type)
        if price is None:
            continue  # Skip if no price found

        est_cost = price * hours_per_month

        # Store breakdown with SKU and Region
        cost_breakdown[s_name] = {
            "cost": round(est_cost, 2),
            "skuName": sku,
            "region": region
        }

        total_cost += est_cost

    return {"total_cost": round(total_cost, 2), "breakdown": cost_breakdown}


# # Example Usage:
# services_list = [
#     {"serviceName": "App Service", "skuName": "B3"},
#     {"serviceName": "Virtual Machines", "skuName": "standard_DC32ds_v3"},
# ]
#
# costs = get_azure_service_cost(services_list, region="East US")
# print(costs)
