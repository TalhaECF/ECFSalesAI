import requests
import re
import os
from pathlib import Path
from docx import Document
import openpyxl
from utils import get_file_content, process_docx_content


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



def add_tasks_to_excel(file_path,hours_estimate, task_titles, project_id, sheet_name="Eng WBS"):
    """
    Loads an Excel file, navigates to a specific sheet, and adds task data in columns H and I,
    starting from H12 and I12.

    :param file_path: Path to the Excel file.
    :param sheet_name: Name of the worksheet to modify.
    """
    try:
        # Load the workbook
        wb = openpyxl.load_workbook(file_path)

        # Select the worksheet
        if sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
        else:
            raise ValueError(f"Sheet '{sheet_name}' not found in the Excel file.")

        # Dummy data for hours and tasks
        hours_estimates = [2, 4, 6, 8, 3, 5]  # List of hours
        task_titles = ["Design UI", "Develop API", "Testing", "Code Review", "Deployment", "Documentation"]

        # Start adding data from H12 and I12
        start_row = 12

        for i, (hours, task) in enumerate(zip(hours_estimates, task_titles)):
            row = start_row + i
            sheet[f"H{row}"] = hours  # Hours estimate (int)
            sheet[f"I{row}"] = task   # Task title (text)

        # Save the updated file
        file_name = f"wbs_{project_id}.xlsx"
        wb.save(file_name)
        print(f"Data successfully added to '{sheet_name}' in {file_path}")

    except Exception as e:
        print(f"Error: {e}")


def create_file(hours_estimate, task_titles, project_id):
    # Call the function
    file_path = "wbs.xlsx"  # Update this with the actual file path
    add_tasks_to_excel(file_path, hours_estimate, task_titles, project_id)
