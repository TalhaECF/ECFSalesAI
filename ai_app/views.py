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
        drive_id = "b!abcdef12345-67890-cdef12345-ghijkl"
        folder_path = "Documents/Uploads"

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


class DiscoveryQuestionnaireView(APIView):
    """
    Fetch the Discovery Questionnaire file for a specific project ID.
    """
    def get(self, request, project_id):
        try:
            site_id = config("SITE_ID")
            # Define the library path for Discovery Questionnaire files
            discovery_library_path = "Discovery Questionnaires"

            # Get access token
            access_token = get_access_token()
            access_token = "eyJ0eXAiOiJKV1QiLCJub25jZSI6Im5WTVNFdlc5WGZKdDVzdHN3bTR3dWkwZFNoWTQ5WnhCUHF5bVY5SXR3NUkiLCJhbGciOiJSUzI1NiIsIng1dCI6InoxcnNZSEhKOS04bWdndDRIc1p1OEJLa0JQdyIsImtpZCI6InoxcnNZSEhKOS04bWdndDRIc1p1OEJLa0JQdyJ9.eyJhdWQiOiIwMDAwMDAwMy0wMDAwLTAwMDAtYzAwMC0wMDAwMDAwMDAwMDAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8wNWUwMzI5Mi02Y2E2LTRmMjYtOGM2Ni00YjFlMGNlNjgwMzcvIiwiaWF0IjoxNzM0OTYwMjUyLCJuYmYiOjE3MzQ5NjAyNTIsImV4cCI6MTczNDk2NDg1MywiYWNjdCI6MCwiYWNyIjoiMSIsImFpbyI6IkFWUUFxLzhZQUFBQWVpWnk3V3FGaGdqSTdYdzJwZkc2NFpiL1lWbnN4eFlrRThNZEZxOXN0MndSc2liWjlyYUV3UXpNems5WHcwVzRtKzY5V3FrakpWWjdBdjhESVlleFUxQ1I3ZTZPVCsyS3F0cmNBTkZoQk5VPSIsImFtciI6WyJwd2QiLCJyc2EiLCJtZmEiXSwiYXBwX2Rpc3BsYXluYW1lIjoiR3JhcGggRXhwbG9yZXIiLCJhcHBpZCI6ImRlOGJjOGI1LWQ5ZjktNDhiMS1hOGFkLWI3NDhkYTcyNTA2NCIsImFwcGlkYWNyIjoiMCIsImRldmljZWlkIjoiY2RmYTg3NDItODQzZi00ODk4LTlmM2EtZDYyYjNkMjZkNTQyIiwiZmFtaWx5X25hbWUiOiJKYWxlZWwiLCJnaXZlbl9uYW1lIjoiVGFsaGEiLCJpZHR5cCI6InVzZXIiLCJpcGFkZHIiOiIyMC4xNzIuNS4yOCIsIm5hbWUiOiJUYWxoYSBKYWxlZWwiLCJvaWQiOiIzYmE2YzBmZC1jNzQzLTQ2NzAtYjNiNS1jMzUxNjRjNDhkZDQiLCJwbGF0ZiI6IjMiLCJwdWlkIjoiMTAwMzIwMDNBRkFEN0VBRSIsInJoIjoiMS5BVmdBa2pMZ0JhWnNKay1NWmtzZURPYUFOd01BQUFBQUFBQUF3QUFBQUFBQUFBQllBRTlZQUEuIiwic2NwIjoiQ2FsZW5kYXJzLlJlYWRXcml0ZSBDaGFubmVsTWVzc2FnZS5TZW5kIENoYXQuUmVhZCBDaGF0LlJlYWRCYXNpYyBDb250YWN0cy5SZWFkV3JpdGUgRGV2aWNlTWFuYWdlbWVudFJCQUMuUmVhZC5BbGwgRGV2aWNlTWFuYWdlbWVudFNlcnZpY2VDb25maWcuUmVhZC5BbGwgRGlyZWN0b3J5LlJlYWQuQWxsIERpcmVjdG9yeS5SZWFkV3JpdGUuQWxsIEZpbGVzLlJlYWRXcml0ZS5BbGwgR3JvdXAuUmVhZFdyaXRlLkFsbCBJZGVudGl0eVJpc2tFdmVudC5SZWFkLkFsbCBNYWlsLlJlYWQgTWFpbC5SZWFkV3JpdGUgTWFpbGJveFNldHRpbmdzLlJlYWRXcml0ZSBOb3Rlcy5SZWFkV3JpdGUuQWxsIG9wZW5pZCBQZW9wbGUuUmVhZCBQbGFjZS5SZWFkIFByZXNlbmNlLlJlYWQgUHJlc2VuY2UuUmVhZC5BbGwgUHJpbnRlclNoYXJlLlJlYWRCYXNpYy5BbGwgUHJpbnRKb2IuQ3JlYXRlIFByaW50Sm9iLlJlYWRCYXNpYyBwcm9maWxlIFJlcG9ydHMuUmVhZC5BbGwgU2l0ZXMuUmVhZFdyaXRlLkFsbCBUYXNrcy5SZWFkV3JpdGUgVXNlci5SZWFkIFVzZXIuUmVhZC5BbGwgVXNlci5SZWFkQmFzaWMuQWxsIFVzZXIuUmVhZFdyaXRlIFVzZXIuUmVhZFdyaXRlLkFsbCBlbWFpbCIsInNpZ25pbl9zdGF0ZSI6WyJkdmNfbW5nZCIsImR2Y19jbXAiLCJrbXNpIl0sInN1YiI6IjZZS2lfa0NucHV4bjFjWXFkVkpDMVJFWnUtZjlOcEcxNTNxQVl0ank4S3ciLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiTkEiLCJ0aWQiOiIwNWUwMzI5Mi02Y2E2LTRmMjYtOGM2Ni00YjFlMGNlNjgwMzciLCJ1bmlxdWVfbmFtZSI6IlRhbGhhLkphbGVlbEBlY2ZkYXRhLmNvbSIsInVwbiI6IlRhbGhhLkphbGVlbEBlY2ZkYXRhLmNvbSIsInV0aSI6Img1QjZaMmFwSWtpeWlHYVRhNlVkQUEiLCJ2ZXIiOiIxLjAiLCJ3aWRzIjpbImI3OWZiZjRkLTNlZjktNDY4OS04MTQzLTc2YjE5NGU4NTUwOSJdLCJ4bXNfY2MiOlsiQ1AxIl0sInhtc19mdGQiOiJ2c01aWnVqMXJTM1ROX1J1aklPd0RxNG4zZTg4Qlp5WksycHU2ZlFwWmZjIiwieG1zX2lkcmVsIjoiMSAyIiwieG1zX3NzbSI6IjEiLCJ4bXNfc3QiOnsic3ViIjoiRnFQSHR5OEt4ME03ODgzRWkxVkpTaWNaX3pxRFNERmxIbURsSXc5ZUFkbyJ9LCJ4bXNfdGNkdCI6MTM2NTQ2ODU2MH0.OT9geAUydTGmNcdncTd8HRyVgUigYzguLZyeWleIS5r5AMq8FVrp1xsfwykgveyIwDluhV0CPHgKKliaLe0tOg7aDgrJ4ZqVGh_17KgKeOoDS7fn395oJeUfVKqX4fVOpQlbK_7JNxA_HWGycfYKOidbl8bjEX46n8u9efrNulx8KeNf6WXSEOA3CatKOCp7T1obJ8F5cgvrggTSwDNrYzb72Fy5RVPUEKou8XJ8CLJjxVsv0vZskJCkfONmwVXA3rdrKRvqj1CtVgr7kWYErNRhYB_fVlM0uVYoHCCXGQiRLonFVCH6ajoI-7oxizRc_2vafWZX3ArJ2yhL7Fgu6A"
            print(f"TOKEN: {access_token}")
            # Fetch the file
            file_data = get_file_by_project_id(
                site_id=site_id,
                library_path=discovery_library_path,
                project_id=project_id,
                access_token=access_token,
            )

            return Response({"file": file_data})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class WBSDocumentView(APIView):
    """
    Fetch the WBS Document file for a specific project ID.
    """
    def get(self, request, project_id):
        try:
            site_id = config("SITE_ID")
            # Define the library path for WBS files
            wbs_library_path = "WBS Documents"

            # Get access token
            access_token = get_access_token()

            # Fetch the file
            file_data = get_file_by_project_id(
                site_id=site_id,
                library_path=wbs_library_path,
                project_id=project_id,
                access_token=access_token,
            )

            return Response({"file": file_data})
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
