import requests
import re
import os
from pathlib import Path
from docx import Document
from .utils import get_file_content, process_docx_content


def get_wbs_content(access_token, item_id):
    url = f"https://graph.microsoft.com/v1.0/drives/b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ434ZGlZGR9TZe60XbJg3Dl/items/{item_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    response = response.json()
    download_url = response.get("@microsoft.graph.downloadUrl", None)
    if not download_url:
        raise "There was an issue while getting the Download URL from Sharepoint"
    file_content_binary = get_file_content(access_token, download_url)
    wbs_content = process_docx_content(binary_content=file_content_binary)

    return wbs_content


def upload_wbs_to_sharepoint(access_token, file_path, project_id):
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }


        # Upload the file
        upload_url = f"https://graph.microsoft.com/v1.0/sites/ecfdata.sharepoint.com,164f5483-ae41-4136-8ec6-8cd9645c947d,d8bd93c5-2a05-4582-90c6-d6ee8c5f409e/drives/b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ434ZGlZGR9TZe60XbJg3Dl/root:/WBS-{project_id}.docx:/content"

        with open(file_path, "rb") as file:
            response = requests.put(upload_url, headers=headers, data=file)

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload file: {response.json()}")

        # Extract the uploaded file's item ID
        item_id = response.json().get("id")

        # Get existing columns
        columns_url = f"https://graph.microsoft.com/v1.0/sites/ecfdata.sharepoint.com,164f5483-ae41-4136-8ec6-8cd9645c947d,d8bd93c5-2a05-4582-90c6-d6ee8c5f409e/drives/b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ434ZGlZGR9TZe60XbJg3Dl/items/{item_id}/listItem/fields"
        print(columns_url)
        fields_response = requests.get(columns_url, headers=headers)

        if fields_response.status_code != 200:
            raise Exception(f"Failed to fetch columns: {fields_response.json()}")

        updated_project_id = {
            "ProjetID":project_id
        }

        # Update the columns
        update_response = requests.patch(columns_url, headers=headers, json=updated_project_id)

        if update_response.status_code != 200:
            raise Exception(f"Failed to update project_id: {update_response.json()}")

    except Exception as e:
        raise Exception(f"Error during SharePoint upload or update: {str(e)}")


def create_upload_wbs(access_token, result, project_id):
    folder_path = Path(".")
    new_doc = Document()

    result = re.sub(r'\*', '', result)

    # Add LLM-generated content to the new document
    new_doc.add_paragraph(result, style='Normal')

    # Save the generated questionnaire
    output_file_path = folder_path / "Generated_Discovery_Questionnaire.docx"
    new_doc.save(output_file_path)

    # Upload to SharePoint
    upload_wbs_to_sharepoint(access_token, output_file_path, project_id)
    # update_current_step(project_id, "Questionnaire Review")

    # Remove the file after successful submission
    os.remove(output_file_path)

    return True
