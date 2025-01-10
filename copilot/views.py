from django.http import JsonResponse
from rest_framework.views import APIView, View
from rest_framework.response import Response
from rest_framework import status
from .utils import *


class CopilotAgentChatAPIView(APIView):

    http_method_names =  ["get"]

    def get(self,request):
        message = request.query_params.get("message")
        bot_response, success = complete_process(message)
        if success:
            return Response({ "response":bot_response}, status=200)

        return Response({"response":bot_response},status=500)
