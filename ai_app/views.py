import re
import time
import logging

from PyPDF2 import PdfReader
from django.http import JsonResponse
from rest_framework.views import APIView, View
from rest_framework.response import Response
from rest_framework import status

from .cost_estimate_utils import get_azure_service_cost
from .utils import *
from decouple import config
import os
import sys
import requests
import openai
from pathlib import Path
from openai import AzureOpenAI
from docx import Document
from .copilot_utils import complete_process
from .wbs_utils import get_wbs_content, create_upload_wbs, read_tasks_from_excel
from .common import CommonUtils, get_summaries_from_text, log_execution_time

# Initialize OpenAI client
client = AzureOpenAI(
    api_key=config("OPENAI_API_KEY"),
    api_version=config("OPENAI_API_VERSION"),
    azure_endpoint = config("OPENAI_API_BASE"),
    azure_deployment=config("DEPLOYMENT_NAME"),
    )


class UploadFileToSharePointView(APIView):
    """
    API View to upload a file to SharePoint.
    """

    def post(self, request):
        """
        Upload a file to a SharePoint folder.
        """
        # Fixed SharePoint details
        site_id = "ecfdata.sharepoint.com,164f5483-ae41-4136-8ec6-8cd9645c947d,d8bd93c5-2a05-4582-90c6-d6ee8c5f409e"
        # Overall Drive ID
        # drive_id = "b!OJdlRo8M0UiIs2YwYMeHdR0hfZPcy2lMp0hCqCJGuD__U3HgclY1SLkSCvo2YRPl"
        # Specific Drive ID ()
        drive_id = "b!g1RPFkGuNkGOxozZZFyUfcWTvdgFKoJFkMbW7oxfQJ5dvO4nOud9SYhRy9y-sa-I"
        folder_path = "Discovery Questionnaires/"

        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Call the utility function to upload the file
            response = upload_file_to_sharepoint(
                site_id, drive_id, folder_path, file.name, file.read()
            )
            return Response(response, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InitialFormResponseView(APIView):
    """
    Fetch the Discovery Questionnaire file for a specific project ID.
    """

    def get(self, request, project_id):
        try:
            site_id = config("SITE_ID")
            # Define the library path for Discovery Questionnaire files
            discovery_library_path = "Documents"

            # Get access token
            access_token = get_access_token()
            # print(f"TOKEN: {access_token}")
            # Fetch the file
            # file_data = get_file_by_project_id(
            #     site_id=site_id,
            #     library_path=discovery_library_path,
            #     project_id=project_id,
            #     access_token=access_token,
            # )

            # return Response({"file": file_data})
            return Response("SUCCESS", status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class DiscoveryQuestionnaireView(APIView):
    """
    Fetch the Discovery Questionnaire file for a specific project ID.
    """
    http_method_names = ['get', 'head', 'post']

    # def get(self, request):
    #     return Response("SUCCESS", status=200)

    def post(self, request):
        try:
            site_id = config("SITE_ID")
            # Define the library path for Discovery Questionnaire files
            discovery_library_path = "Discovery Questionnaires"

            # Get project_id from the request body
            project_id = request.data.get("project_id")
            if not project_id:
                return Response({"error": "Project ID is required."}, status=400)

            # Get access token
            # access_token = get_access_token()
            # print(f"TOKEN: {access_token}")

            # Fetch the file
            # file_data = get_file_by_project_id(
            #     site_id=site_id,
            #     library_path=discovery_library_path,
            #     project_id=project_id,
            #     access_token=access_token,
            # )

            # return Response({"file": file_data})
            return Response("SUCCESS", status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class WBSDocumentView(APIView):
    """
    Fetch the WBS Document file for a specific project ID.
    """

    http_method_names = ['get', 'head', 'post']
    def post(self, request):
        try:

            user_remarks = request.data.get("message")
            access_token = get_access_token()
            project_id = request.data.get("project_id")
            wbs_item_id = request.data.get("wbs_item_id", None)

            questionnaire_content = get_discovery_questionnaire(access_token, project_id)

            costs = self.cost_estimation(questionnaire_content)
            update_current_step(project_id, "Cost Estimation - WBS", key="LoggingStatus")
            prompt_zero = (f"Return all the solution plays in a list in json, The key must be 'SolutionPlays' and in values keep a list like ['Solution PLay1', 'Solution Play2']"
                           f"Figure out Solution Plays from this filled Discovery Questionnaire Content{questionnaire_content}")
            solution_plays_list = gpt_response_for_sp(client, prompt_zero)
            copilot_prompt = f"""
                                Solution plays: {solution_plays_list}
                                Give all helpful MS Docs learning links along with Technical Topics name related to these Solution plays
                                Make sure to add helpful links of relevant docs
                            """
            copilot_response, success = complete_process(copilot_prompt)
            update_current_step(project_id, "Copilot Response - WBS", key="LoggingStatus")
            summarized_content = get_summaries_from_text(client, copilot_response)
            copilot_response = f"{copilot_response}\n Here is the more context: {summarized_content}"

            if user_remarks != "":
                wbs_data = get_wbs_content(access_token, wbs_item_id)
                prompt = CommonUtils.load_prompt_with_remarks(user_remarks, copilot_response,
                                                              questionnaire_content, wbs_data)
                self.wbs_process(access_token, prompt, project_id, costs)
                return Response("SUCCESS", status=200)

            prompt = CommonUtils.load_prompt_without_remarks(questionnaire_content, copilot_response)
            self.wbs_process(access_token, prompt, project_id, costs)

            return Response("SUCCESS", status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def wbs_process(self, access_token, prompt, project_id, costs):
        result = CommonUtils.gpt_response_json(client, prompt)
        update_current_step(project_id, "OpenA API Response- WBS", key="LoggingStatus")
        create_upload_wbs(access_token, result, project_id, costs)
        update_current_step(project_id, "WBS Process Initiated")
        update_current_step(project_id, "WBS uploaded - WBS", key="LoggingStatus")
        return True

    @log_execution_time
    def cost_estimation(self, questionnaire_content):
        costs = None
        cost_estimation_prompt = """
        Provide a detailed cost estimation for the following Azure services (only East US)
        For each service, include:
        - Service Name
        - Cost in USD
        - SKU Name (e.g., 'Standard_D2s_v3', 'Hot LRS')
        - Region (e.g., 'East US', 'West Europe')
        Return the data in JSON format structured like this:

        {
  "servicesList": [
    {
      "serviceName": "App Service",
      "skuName": "B1",
      "region": "East US",
      "tier": ""
    },
    {
      "serviceName": "Virtual Machines",
      "skuName": "Standard_D2s_v3",
      "region": "East US",
      "tier": "Standard"
        }
      ]
    }

     Instructions:
    - Make sure the response is in JSON
    - Add all relevant serviceName and the appropriate skuName, region and tier
    - The sample serviceName, skuName, region, and tier are just example/reference
    - Make sure the service and skuName must be available in that region under that tier
    - The services will be used to estimate cost, so make sure that we have Microsoft list of services
        """

        result_json = eval(CommonUtils.gpt_response_json(client, cost_estimation_prompt))
        services = result_json.get("servicesList", None)
        if services:
            costs = get_azure_service_cost(services)

        return costs


class OAuthRedirectView(View):
    """
    Handles the redirect URI for Microsoft OAuth authentication.
    """

    def get(self, request):
        code = request.GET.get('code')
        error = request.GET.get('error')

        tenant_id = config("TENANT_ID")

        if error:
            return JsonResponse({"error": error}, status=400)

        if not code:
            return JsonResponse({"error": "Authorization code not provided"}, status=400)

        # Exchange the authorization code for an access token
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": config("CLIENT_ID"),
            "client_secret": config("CLIENT_SECRET"),
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"https://<ngrok-subdomain>.ngrok.io/redirect/",
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(token_url, data=data, headers=headers)

        if response.status_code == 200:
            token_data = response.json()
            return JsonResponse({"access_token": token_data.get("access_token")})
        else:
            return JsonResponse({"error": response.json()}, status=response.status_code)




class DiscoveryQuestionnaireAPIView(APIView):
    """
    API View to handle document parsing and generating discovery questionnaires in Markdown format.
    """
    http_method_names = ['get',  'post']

    def post(self, request, *args, **kwargs):
        user_remarks = request.data.get("message")
        access_token = get_access_token()
        project_id = request.data.get("project_id")
        item_id = request.data.get("item_id")
        initial_form_content = get_initial_form_by_search(access_token, item_id)

        taxonomy_json = ""
        message, file_path, success = taxonomy_processing(client, access_token)

        if not success:
            print(f'Using the already existing JSON content because {message}')
            file_path = "response.json"
        taxonomy_json = read_json_file(file_path)

        # Folder path where documents are stored
        folder_path = Path(".")

        if not folder_path.exists() or not folder_path.is_dir():
            return Response(
                {"error": "The 'Dummy Docs' folder does not exist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Read and parse documents
            all_text, discovery_questionnaire_text = read_and_parse_documents(folder_path)
            prompt_zero = f"Return all the solution plays in a list in json, The key must be 'SolutionPlays' and in values keep a list like ['Solution Play1', 'Solution Play2'], find Solution Plays from here: {initial_form_content}"
            solution_plays_list = gpt_response_for_sp(client, prompt_zero)
            copilot_prompt = f"""
                    Solution plays: {solution_plays_list}
                    Give all helpful MS Docs learning links along with Technical Topics name related to these Solution plays
                    Make sure to add helpful links of relevant docs
                """
            copilot_response, success = complete_process(copilot_prompt)

            # if user_remarks != "":
            #     questionnaire_content_binary, flag = get_discovery_questionnaire(access_token, project_id)
            #     questionnaire_content = process_docx_content(questionnaire_content_binary)
            #     print(questionnaire_content)
            #
            #     if flag:
            #         user_remarks_prompt = f"""
            #         Here is the discovery questionnaire content: {questionnaire_content}
            #         Make changes to it based on these user remarks: {user_remarks}
            #
            #         Instructions:
            #         - Here is the additional information for updating the discovery questionnaire based on user remarks: {all_text}
            #         - Ensure that the structure and format of the provided discovery questionnaire are followed precisely.
            #         - Write the output directly, do not add any meta content, add the content of discovery questionnaire ONLY
            #         - Output only the questionnaire content, formatted as a numbered list with properly labeled options in Doc format
            #         - Keep the provided discovery questionnaire content and only updated based on user remarks
            #         - Questions should be relevant to the Solution Play(s) mentioned here {solution_plays_list}
            #         """
            #
            #         response = client.chat.completions.create(
            #             model="gpt-4o-mini",
            #             max_tokens=10000,
            #             messages=[{"role": "user", "content": user_remarks_prompt}]
            #         )
            #         result = response.choices[0].message.content.strip()
            #
            #         new_doc = Document()
            #
            #         result = re.sub(r'\*', '', result)
            #
            #         # Add LLM-generated content to the new document
            #         new_doc.add_paragraph(result, style='Normal')
            #
            #         # Save the generated questionnaire
            #         output_file_path = folder_path / "Generated_Discovery_Questionnaire.docx"
            #         new_doc.save(output_file_path)
            #
            #         # Upload to SharePoint
            #         upload_questionnaire_to_sharepoint(output_file_path, project_id)
            #         update_current_step(project_id, "Questionnaire Review")
            #
            #         # Remove the file after successful submission
            #         os.remove(output_file_path)
            #
            #         return Response(
            #             {
            #                 "message": "Generated discovery questionnaire successfully."
            #             },
            #             status=status.HTTP_200_OK,
            #         )

            prompt = f""""
                Based on the following discovery questionnaire, generate a new discovery questionnaire tailored specifically for the Solution Play(s) mentioned in this list: {solution_plays_list}\n 
                \n\nSample Discovery Questionnaire:\n{discovery_questionnaire_text}\n\n
                For context, here is the Initial Form response with the transcript:\n\n {copilot_response} \n
                Here is some more context which has solution plays: \n{taxonomy_json}\n
                User Notes (must be followed): {user_remarks}

                Instructions:
                - Make sure to complete the discovery questionnaire focusing exclusively on the Solution Play(s) mentioned in the Form Response and User Notes
                - Questions should be relevant to the Solution Play(s) mentioned.
                - Use clear numbering for each question and proper formatting for multiple-choice options (e.g., (1), (2), etc.).
                - Ensure that the structure and format of the sample discovery questionnaire are followed precisely.
                - Output only the questionnaire content, formatted as a numbered list with properly labeled options in Docx format
                """

            deployment_name_model = config("DEPLOYMENT_NAME")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=10000,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content.strip()

            new_doc = Document()

            result = re.sub(r'\*', '', result)

            # Add LLM-generated content to the new document
            new_doc.add_paragraph(result, style='Normal')

            # Save the generated questionnaire
            output_file_path = folder_path / "Generated_Discovery_Questionnaire.docx"
            new_doc.save(output_file_path)

            # Upload to SharePoint
            upload_questionnaire_to_sharepoint(output_file_path, project_id)
            update_current_step(project_id, "Questionnaire Review")

            # Remove the file after successful submission
            os.remove(output_file_path)

            return Response(
                {
                    "message": "Generated discovery questionnaire successfully."
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PromptResponseAPIView(APIView):
    """
    API View to handle user queries/prompts and return AI-generated responses.
    """
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        prompt = request.data.get("prompt")

        if not prompt:
            return Response(
                {"error": "The 'prompt' field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Call OpenAI GPT model to get a response
            response = openai.Completion.create(
                engine="text-davinci-003",  # Replace with your model
                prompt=prompt,
                max_tokens=200,
            )
            generated_text = response.choices[0].text.strip()

            return Response(
                {"response": generated_text},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SharePointFileParserView(APIView):
    http_method_names = ['post']

    def post(self, request):

        try:
            access_token = get_access_token()
            message, file_path, success = taxonomy_processing(client, access_token)

            if not success:
                return Response(message, status=404)

            return Response(message, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)