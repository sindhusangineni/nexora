from django.conf import settings
from rest_framework import serializers


class TokenRefreshSerializer(serializers.Serializer):
    def validate(self, attrs):
        request = self.context.get("request")
        cookie_name = getattr(settings, "AUTH_COOKIE_NAME", "refresh_token")
        cookie_token = request.COOKIES.get(cookie_name) if request else None

        if not cookie_token:
            raise serializers.ValidationError({"refresh": ["Refresh token cookie is required."]})

        attrs["refresh_token"] = cookie_token
        return attrs

