import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.managementpartner import ManagementPartnerClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Azure Authentication
def get_management_partner_client():
    credential = DefaultAzureCredential()
    client = ManagementPartnerClient(credential)
    return client

# Azure AI Search Configuration
search_client = SearchClient(
    endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
    index_name="partner-solutions",
    credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_KEY'))
)

def create_solution_search_index(partner_client):
    """Create Azure AI Search index with partner solutions"""
    # Assuming you have a method to list customers and their solutions
    customers = partner_client.partner.list()  # Adjust this line based on actual method

    solution_docs = []
    for customer in customers:
        solutions = partner_client.solutions.list(customer.id)  # Adjust this line based on actual method
        for solution in solutions:
            doc = {
                "id": solution.id,
                "customer": customer.name,  # Adjust based on actual attribute
                "title": solution.name,
                "description": solution.description,
                "keywords": ", ".join(solution.tags),
                "category": solution.category,
                "implementation_date": solution.created_date,
                "success_metrics": solution.metrics
            }
            solution_docs.append(doc)

    search_client.upload_documents(documents=solution_docs)

def find_relevant_solutions(keywords, solution_plays):
    """Hybrid search combining keywords and solution play context"""
    search_results = search_client.search(
        search_text=keywords,
        filter=f"search.ismatch('{solution_plays}', 'category')",
        query_type="semantic",
        semantic_configuration_name="partner-semantic-config",
        query_language="en-US",
        query_speller="lexicon",
        top=10
    )

    results = []
    for result in search_results:
        results.append({
            "solution_id": result["id"],
            "title": result["title"],
            "relevance_score": result["@search.score"],
            "customer": result["customer"],
            "key_metrics": result["success_metrics"]
        })

    return results

def get_solution_details(solution_id):
    """Retrieve full solution details from Partner Center"""
    partner_client = get_management_partner_client()
    solution = partner_client.solutions.get(solution_id)  # Adjust this line based on actual method

    return {
        "technical_implementation": solution.technical_details,
        "licensing_model": solution.licensing_info,
        "reference_architecture": solution.architecture_diagram_url,
        "customer_success_story": solution.case_study
    }

def generate_ai_response(query, keywords):
    """End-to-end query processing"""
    relevant_solutions = find_relevant_solutions(keywords, query)
    detailed_responses = []

    for solution in relevant_solutions:
        details = get_solution_details(solution["solution_id"])
        detailed_responses.append({
            **solution,
            "details": details
        })

    return detailed_responses

# Test Partner Center Connection
if __name__ == "__main__":
    partner_client = get_management_partner_client()
    # Test the connection by listing partners
    partners = partner_client.partner.list()  # Adjust this line based on actual method
    assert partners is not None, "Connection failed!"

    # Initialize search index (run once)
    create_solution_search_index(partner_client)

    # Sample query
    response = generate_ai_response(
        query="Azure Migration",
        keywords="hybrid cloud, cost optimization, security compliance"
    )

    print(f"Found {len(response)} relevant solutions:")
    for sol in response:
        print(f"\nSolution: {sol['title']}")
        print(f"Customer: {sol['customer']}")
        print(f"Relevance Score: {sol['relevance_score']:.2f}")
