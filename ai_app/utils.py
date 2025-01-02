import os
import json
import requests
from Tools.scripts.generate_opcode_h import header
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


def upload_questionnaire_to_sharepoint(file_path, project_id):
    try:
        access_token = get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }


        # Upload the file
        upload_url = f"https://graph.microsoft.com/v1.0/sites/ecfdata.sharepoint.com,164f5483-ae41-4136-8ec6-8cd9645c947d,d8bd93c5-2a05-4582-90c6-d6ee8c5f409e/drives/b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ7BI2nybhy9Qp-2Uu0XUmby/root:/Discovery Questionnaire-{project_id}.docx:/content"

        with open(file_path, "rb") as file:
            response = requests.put(upload_url, headers=headers, data=file)

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload file: {response.json()}")

        # Extract the uploaded file's item ID
        item_id = response.json().get("id")

        # Get existing columns
        columns_url = f"https://graph.microsoft.com/v1.0/sites/ecfdata.sharepoint.com,164f5483-ae41-4136-8ec6-8cd9645c947d,d8bd93c5-2a05-4582-90c6-d6ee8c5f409e/drives/b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ7BI2nybhy9Qp-2Uu0XUmby/items/{item_id}/listItem/fields"
        fields_response = requests.get(columns_url, headers=headers)

        if fields_response.status_code != 200:
            raise Exception(f"Failed to fetch columns: {fields_response.json()}")

        updated_project_id = {
            "ProjectId":project_id
        }

        # Update the columns
        update_response = requests.patch(columns_url, headers=headers, json=updated_project_id)

        if update_response.status_code != 200:
            raise Exception(f"Failed to update project_id: {update_response.json()}")

    except Exception as e:
        raise Exception(f"Error during SharePoint upload or update: {str(e)}")


def update_current_step(project_id, current_step):
    """
    Updates the CurrentStep field in the Project list for the specified project_id.
    """
    try:
        access_token = get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Update URL for CurrentStep
        update_url = f"https://graph.microsoft.com/v1.0/sites/ecfdata.sharepoint.com,164f5483-ae41-4136-8ec6-8cd9645c947d,d8bd93c5-2a05-4582-90c6-d6ee8c5f409e/lists/12e93f47-8fde-47ef-9d8c-30864859fa02/items/{project_id}/fields"
        update_body = {"CurrentStep": current_step}

        # PATCH request to update CurrentStep
        response = requests.patch(update_url, headers=headers, json=update_body)

        if response.status_code != 200:
            raise Exception(f"Failed to update CurrentStep: {response.json()}")

    except Exception as e:
        raise Exception(f"Error updating CurrentStep: {str(e)}")


def get_sharepoint_items(access_token, drive_url):
    """Fetch items from the SharePoint drive URL."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(drive_url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_taxonomy_item_id(access_token, items):
    headers = {"Authorization": f"Bearer {access_token}",}
    item_ids = [i["id"] for i in items["value"]]
    download_urls = [i["@microsoft.graph.downloadUrl"] for i in items["value"]]

    for ind, item_id in enumerate(item_ids):
        url = f"https://graph.microsoft.com/v1.0/drives/b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ5wiSqDwOdQRomugUc4T4s7/items/{item_id}/listItem/fields"
        response = requests.get(url, headers=headers)
        values = response.json()
        if "isParsed" in values:
            if values["isParsed"] == False:
                return item_id, download_urls[ind]
    return -1, ""

def get_file_content(access_token, download_url):
    """Download the file content from the provided URL."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(download_url, headers=headers)
    response.raise_for_status()
    return response.content


def parse_pdf_content(file_content):
    """Parse the content of a PDF file."""
    with open("temp.pdf", "wb") as f:
        f.write(file_content)
    reader = PdfReader("temp.pdf")
    content = "\n".join([page.extract_text() for page in reader.pages])
    os.remove("temp.pdf")
    return content


def send_to_gpt(client, parsed_content):
    """Send parsed content to GPT for a response."""
    prompt = (
        f"I want the response in JSON format. Here is the content: \n{parsed_content}\n"
        f"Please structure the JSON with keys named 'solution_plays' and include in the values the technical capabilities along with a description of each."
        f"Make sure to add all Solution Plays from the content into Json keys"
    )
    response = client.chat.completions.create(
        model="gpt-4",
        max_tokens=2000,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


def save_response_to_json(data, file_path):
    """Save the GPT response to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def set_is_parsed_false(access_token, item_id):
    url = f"https://graph.microsoft.com/v1.0/drives/b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ5wiSqDwOdQRomugUc4T4s7/items/{item_id}/listItem/fields"
    headers = {"Authorization": f"Bearer {access_token}"}
    fields = { "isParsed": "True" }
    response = requests.patch(url,json=fields ,headers=headers)
    response.raise_for_status()
    if response.status_code == "200":
        return True
    return False


def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"The file at {file_path} does not exist.")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Error decoding JSON: {e.msg}", e.doc, e.pos)


def taxonomy_processing(client, access_token):
    drive_url = "https://graph.microsoft.com/v1.0/drives/b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ5wiSqDwOdQRomugUc4T4s7/root/children"
    items = get_sharepoint_items(access_token, drive_url)
    if len(items) == 0:
        return "No Taxonomy file found (or) All files have already been processed!", "", False

    item_id, download_url = get_taxonomy_item_id(access_token, items)
    if item_id == -1:
        return "No Taxonomy file found (or) All files have already been processed!", "", False
    file_content = get_file_content(access_token, download_url)
    set_is_parsed_false(access_token, item_id)

    parsed_content = parse_pdf_content(file_content)
    gpt_response = send_to_gpt(client, parsed_content)

    json_file_path = "response.json"
    save_response_to_json(eval(gpt_response), json_file_path)
    return "File processed and response saved", json_file_path, True
