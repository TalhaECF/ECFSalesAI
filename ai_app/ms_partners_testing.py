import requests
from decouple import config
from msal import ConfidentialClientApplication

# Microsoft Partner Center API Credentials
CLIENT_ID = config("AZURE_CLIENT_ID")
CLIENT_SECRET = config("AZURE_CLIENT_SECRET")
TENANT_ID = config("AZURE_TENANT_ID")

# Microsoft Authentication & API Endpoints
AUTHORITY_URL = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://api.partnercenter.microsoft.com/.default"]  # Corrected scope
BASE_URL = "https://api.partnercenter.microsoft.com"

# Function to get the access token
# def get_access_token():
#     app = ConfidentialClientApplication(CLIENT_ID, CLIENT_SECRET, authority=AUTHORITY_URL)
#     token_response = app.acquire_token_for_client(scopes=SCOPE)
#
#     if "access_token" in token_response:
#         return token_response["access_token"]
#     else:
#         raise Exception(f"Error obtaining access token: {token_response.get('error_description')}")

# Function to make API requests
def make_api_request(endpoint, method="GET", data=None):
    from utils import get_access_token
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    url = f"{BASE_URL}{endpoint}"
    response = requests.request(method, url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

# Function to fetch customers
def get_customers():
    return make_api_request("/v1/customers")

# Function to fetch a specific customer
def get_customer(customer_id):
    return make_api_request(f"/v1/customers/{customer_id}")

# Function to fetch subscriptions of a customer
def get_customer_subscriptions(customer_id):
    return make_api_request(f"/v1/customers/{customer_id}/subscriptions")

# Function to create a new customer
def create_customer(company_name, email, currency="USD", culture="en-US"):
    customer_data = {
        "companyProfile": {"companyName": company_name},
        "billingProfile": {"culture": culture, "currency": currency, "email": email}
    }
    return make_api_request("/v1/customers", method="POST", data=customer_data)

# === TEST FUNCTIONS ===
if __name__ == "__main__":
    try:
        print("\nFetching customers...")
        customers = get_customers()
        print(customers)

        if customers.get("items"):
            first_customer_id = customers["items"][0]["id"]
            print(f"\nFetching details for Customer ID: {first_customer_id}")
            customer_details = get_customer(first_customer_id)
            print(customer_details)

            print(f"\nFetching subscriptions for Customer ID: {first_customer_id}")
            subscriptions = get_customer_subscriptions(first_customer_id)
            print(subscriptions)
        else:
            print("\nNo customers found.")

        print("\nCreating a new customer...")
        new_customer = create_customer("Test Company", "test@example.com")
        print(new_customer)

    except Exception as e:
        print("Error:", str(e))