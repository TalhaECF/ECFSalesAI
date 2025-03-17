import ijson


def get_service_app_records(file_path = "cost_estimation.json", concerned_regions=["East US", "East US 2", "Central US"],
                            service_name="Azure App Service"):
    """
    Efficiently reads a huge JSON file (cost_estimation.json) and retrieves records for the specified service
    (default "App Service") that belong to one of the concerned regions.

    The function uses a streaming parser (ijson) to avoid loading the entire file into memory.

    :param file_path: Path to the JSON file.
    :param concerned_regions: List of region strings (e.g. ["East US", "East US 2", "Central US"]).
    :param service_name: The service to filter by (default "App Service").
    :return: List of filtered records.
    """
    # Normalize concerned regions for comparison (e.g. "East US" -> "eastus")
    normalized_regions = {region.replace(" ", "").lower() for region in concerned_regions}

    matching_records = []

    with open(file_path, "r") as f:
        # Use ijson to iterate over each item in the "Items" list.
        items = ijson.items(f, "Items.item")
        for item in items:
            # Check if the record matches the service name.
            if item.get("serviceName") != service_name:
                continue

            # Normalize the item's region (armRegionName) and check against our concerned regions.
            item_region = item.get("armRegionName", "").lower()
            if item_region in normalized_regions:
                matching_records.append(item)

    return matching_records


# Example usage:
if __name__ == "__main__":
    # file_path = "cost_estimation.json"
    records = get_service_app_records()
    print("Matching records:")
    for rec in records:
        print(rec)
