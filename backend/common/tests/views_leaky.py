"""A deliberately insecure view used only to prove the authorization harness fails."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class LeakyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Intentionally returns every user's rows regardless of ownership.
        from apps.accounts.models import User

        return Response({"results": [{"id": str(user.pk)} for user in User.objects.all()]})
