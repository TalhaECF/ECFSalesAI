import os
import requests
from decouple import config
from PyPDF2 import PdfReader
from docx import Document


def get_access_token():
    """
    Generate an access token using client credentials flow.
    """
    tenant_id = config("TENANT_ID")
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': config("CLIENT_ID"),
        'client_secret':config("CLIENT_SECRET"),
        'scope': 'https://graph.microsoft.com/.default',
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Unable to get access token \n Error: {response.text}")


def upload_file_to_sharepoint(site_id, drive_id, folder_path, file_name, file_content):
    """
    Upload a file to SharePoint in the specified folder.
    """
    try:
        access_token = get_access_token()
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{folder_path}/{file_name}:/content"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/octet-stream',
        }

        response = requests.put(url, headers=headers, data=file_content)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to upload file: {response.json()}")
    except Exception as e:
        raise Exception(f"Error uploading file: {str(e)}")


# def get_file_from_sharepoint(site_id, drive_id, file_path):
#     """
#     Fetch a file from SharePoint based on its path.
#     """
#     try:
#         access_token = get_access_token()
#         url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{file_path}:/content"
#         headers = {'Authorization': f'Bearer {access_token}'}
#
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             return response.content  # Return the raw file content
#         else:
#             raise Exception(f"Failed to retrieve file: {response.json()}")
#     except Exception as e:
#         raise Exception(f"Error retrieving file: {str(e)}")


def get_file_from_sharepoint(site_id, file_path, access_token):
    """
    Fetches a specific file from a predefined SharePoint path.
    """
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{file_path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch file: {response.json()}")


def get_file_by_project_id(site_id, library_path, project_id, access_token):
    """
    Fetches a file from a SharePoint document library where the project_id matches a file's metadata or name.
    """
    # Microsoft Graph API URL to list items in the library
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{library_path}:/children"
    print(f"URL: {url}")
    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch all items in the document library
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch files: {response.json()}")

    # Filter files based on the project_id in the metadata or file name
    items = response.json().get('value', [])
    for item in items:
        if item.get('file') and item.get('name') and project_id in item.get('name'):
            return item

    # If no matching file is found
    raise Exception(f"No file found for project ID: {project_id}")



def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def extract_text_from_docx(file_path):
    """Extract text from a Word document."""
    doc = Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    return text


def read_and_parse_documents(folder_path):
    """Read all PDF and DOCX files from the folder and return concatenated text."""
    all_text = ""
    discovery_questionnaire_text = None

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if file_name.lower().endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif file_name.lower().endswith(".docx"):
            text = extract_text_from_docx(file_path)
        else:
            continue  # Skip non-PDF and non-DOCX files

        # Check for the Discovery Questionnaire document
        if "discovery questionnaire" in file_name.lower():
            discovery_questionnaire_text = text
        else:
            all_text += text + "\n"

    return all_text, discovery_questionnaire_text

