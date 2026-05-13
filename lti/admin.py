from django.contrib import admin
from .models import LTIRegistration, LTIResourceMapping, LTISession
from .utils import generate_rsa_keypair


@admin.register(LTIRegistration)
class LTIRegistrationAdmin(admin.ModelAdmin):
    list_display = ("name", "issuer", "client_id", "created_at")
    readonly_fields = ("tool_key_id",)

    def save_model(self, request, obj, form, change):
        # Auto-generate RSA key pair if not already set
        if not obj.tool_private_key or not obj.tool_public_key:
            private_pem, public_pem = generate_rsa_keypair()
            obj.tool_private_key = private_pem
            obj.tool_public_key = public_pem
        super().save_model(request, obj, form, change)


@admin.register(LTIResourceMapping)
class LTIResourceMappingAdmin(admin.ModelAdmin):
    list_display = ("resource_link_id", "course", "registration", "lineitem_url")
    list_filter = ("registration",)


@admin.register(LTISession)
class LTISessionAdmin(admin.ModelAdmin):
    list_display = ("user", "lti_user_id", "resource_mapping", "created_at")
    list_filter = ("registration",)
    readonly_fields = ("id", "created_at")
