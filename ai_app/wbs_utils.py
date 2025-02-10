import requests
import re
import os
from pathlib import Path
from docx import Document
from decouple import config
import openpyxl
from .utils import get_file_content, process_docx_content


def get_wbs_content(access_token, item_id):
    wbs_drive_id = config("WBS_DRIVE")
    url = f"https://graph.microsoft.com/v1.0/drives/{wbs_drive_id}/items/{item_id}"
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

        site_id = config("SITE_ID")
        wbs_drive_id = config("WBS_DRIVE")
        # Upload the file
        upload_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{wbs_drive_id}/root:/WBS-{project_id}.xlsx:/content"

        with open(file_path, "rb") as file:
            response = requests.put(upload_url, headers=headers, data=file)

        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload file: {response.json()}")

        # Extract the uploaded file's item ID
        item_id = response.json().get("id")

        # Get existing columns
        columns_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{wbs_drive_id}/items/{item_id}/listItem/fields"
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
    output_file_path = create_file(result, project_id)

    # Upload to SharePoint
    upload_wbs_to_sharepoint(access_token, output_file_path, project_id)
    # update_current_step(project_id, "Questionnaire Review")

    # Remove the file after successful submission
    os.remove(output_file_path)

    return True


def add_tasks_to_excel(file_path, phases_data, project_id, sheet_name="Eng WBS"):
    """
    Loads an Excel file, navigates to a specific sheet, and adds task data from the phases_data dictionary,
    inserting hours and task titles into specific columns for each phase.

    :param file_path: Path to the Excel file.
    :param phases_data: Dictionary containing phase-wise hours and tasks.
    :param project_id: Project ID for naming the file.
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

        # Define starting row and column mappings for each phase
        phases_columns = {
            "phase1": ["C", "D", 11],
            "phase2": ["H", "I", 9],
            "phase3": ["M", "N", 9],
            "phase4": ["R", "S", 9]
        }

        # Iterate over each phase and add data to corresponding columns
        for phase, (hours_col, task_col, start_row) in phases_columns.items():
            if phase in phases_data:
                hours_list = phases_data[phase].get("hours", [])
                tasks_list = phases_data[phase].get("tasks", [])

                for i, (hours, task) in enumerate(zip(hours_list, tasks_list)):
                    row = start_row + i
                    sheet[f"{hours_col}{row}"] = hours  # Hours estimate
                    sheet[f"{task_col}{row}"] = task  # Task title

        # Save the updated file
        file_name = f"wbs_{project_id}.xlsx"
        wb.save(file_name)
        print(f"Data successfully added to '{sheet_name}' in {file_name}")
        return file_name

    except Exception as e:
        print(f"Error: {e}")
        return None

def create_file(ai_response, project_id):
    file_path = "ai_app/wbs.xlsx"
    json_ai_response = eval(ai_response)
    file_name = add_tasks_to_excel(file_path, json_ai_response, project_id)
    return file_name
