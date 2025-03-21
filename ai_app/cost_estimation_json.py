import json


def get_service_app_records(file_path="cost_estimation.json",
                            concerned_regions=["East US", "East US 2", "Central US"],
                            service_name="Azure App Service"):
    """
    Reads a JSON file (cost_estimation.json) and retrieves records for the specified service
    (default "Azure App Service") that belong to one of the concerned regions.

    :param file_path: Path to the JSON file.
    :param concerned_regions: List of region strings (e.g. ["East US", "East US 2", "Central US"]).
    :param service_name: The service to filter by (default "Azure App Service").
    :return: List of filtered records.
    """
    # Normalize concerned regions for comparison (e.g. "East US" -> "eastus")
    normalized_regions = {region.replace(" ", "").lower() for region in concerned_regions}

    matching_records = []

    with open(file_path, "r") as f:
        data = json.load(f)  # Load entire JSON into memory

        # Ensure "Items" key exists and is a list
        for item in data.get("Items", []):
            if item.get("serviceName") == service_name and item.get("armRegionName", "").replace(" ",
                                                                                                 "").lower() in normalized_regions:
                matching_records.append(item)

    return matching_records


# Example usage
# if __name__ == "__main__":
#     records = get_service_app_records()
#     print("Matching records:")
#     for rec in records:
#         print(rec)
