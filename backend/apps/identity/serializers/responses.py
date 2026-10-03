from rest_framework import serializers


class UserResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField(help_text="Unique user identifier.")
    email = serializers.EmailField(help_text="User email address.")
    email_verified = serializers.BooleanField(
        help_text="Indicates whether the email address has been verified."
    )
    roles = serializers.ListField(
        child=serializers.CharField(),
        help_text="Assigned platform roles (e.g., student, superadmin).",
    )


class RegistrationResponseSerializer(serializers.Serializer):
    message = serializers.CharField(
        default="User registered successfully.",
        help_text="Confirmation message.",
    )
    user = UserResponseSerializer(help_text="Registered user profile.")


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="Short-lived JWT access token.")
    user = UserResponseSerializer(help_text="Authenticated user profile.")


class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField(
        help_text="Newly issued short-lived JWT access token."
    )


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Status or confirmation message.")
