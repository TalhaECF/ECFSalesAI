from django.http import JsonResponse
from rest_framework.views import APIView, View
from rest_framework.response import Response
from rest_framework import status
from .utils import upload_file_to_sharepoint, get_file_by_project_id, get_access_token
from decouple import config
import requests


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
    def post(self, request):
        try:
            site_id = config("SITE_ID")
            # Define the library path for Discovery Questionnaire files
            discovery_library_path = "Documents"

            # Get project_id from the request body
            project_id = request.data.get("project_id")
            if not project_id:
                return Response({"error": "Project ID is required."}, status=400)

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


class WBSDocumentView(APIView):
    """
    Fetch the WBS Document file for a specific project ID.
    """
    def post(self, request):
        try:
            site_id = config("SITE_ID")
            # Define the library path for WBS files
            wbs_library_path = "WBS Documents"

            # Get project_id from the request body
            project_id = request.data.get("project_id")
            if not project_id:
                return Response({"error": "Project ID is required."}, status=400)

            # Get access token
            access_token = get_access_token()

            # Fetch the file
            # file_data = get_file_by_project_id(
            #     site_id=site_id,
            #     library_path=wbs_library_path,
            #     project_id=project_id,
            #     access_token=access_token,
            # )

            # return Response({"file": file_data})
            return Response("SUCCESS", status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


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
