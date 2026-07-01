from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.permissions import CanAccessPowerBIEmbed

from .services import powerbi_service


class EmbedConfigView(APIView):
    """
    Embed configuration for admin, HOD, faculty, and student users.
    Returns success=False (HTTP 200) when embedding is unavailable so the UI
    can show setup instructions without treating it as an auth error.
    """

    permission_classes = [IsAuthenticated, CanAccessPowerBIEmbed]

    def get(self, request):
        config = powerbi_service.get_embed_config(request.user)
        return Response(config, status=status.HTTP_200_OK)
