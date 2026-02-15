# accounts/api/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from ..services.permission_resolver import permission_resolver
from ..services.audit_logger import PermissionAuditLogger
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_page(60)  # Cache API response for 1 minute
def effective_permissions_api(request, role=None):
    """
    API endpoint for NodeJS to fetch effective permissions
    GET /api/permissions/effective/MANAGER/
    """
    try:
        # Resolve effective permissions
        effective_permissions = permission_resolver.resolve_permissions()
        
        if role:
            # Single role request
            if role not in effective_permissions:
                return Response(
                    {"error": f"Role '{role}' not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            role_data = {
                "role": role,
                "domains": effective_permissions[role],
                "inherited_from": get_inherited_from(role),
                "protected": role in ['EXEC', 'ADMIN', 'FINANCE'],
                "business_logic_enforced": True,
                "cache_timestamp": cache.get("permissions_cache_timestamp"),
                "version": "2.0"
            }
            
            # Log API access for audit
            PermissionAuditLogger.log_api_access(
                request.user, 
                f"API fetch for role {role}",
                client_ip=get_client_ip(request)
            )
            
            return Response(role_data)
        
        else:
            # Bulk request - all roles
            bulk_data = {
                "timestamp": cache.get("permissions_cache_timestamp"),
                "version": "2.0",
                "roles": {}
            }
            
            for role_name, permissions in effective_permissions.items():
                bulk_data["roles"][role_name] = {
                    "domains": permissions,
                    "protected": role_name in ['EXEC', 'ADMIN', 'FINANCE'],
                    "inherited_from": get_inherited_from(role_name)
                }
            
            return Response(bulk_data)
            
    except Exception as e:
        logger.error(f"Permission API error: {str(e)}", exc_info=True)
        return Response(
            {"error": "Internal server error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_permission_api(request):
    """
    Validate if a role has specific permission
    POST /api/permissions/validate/
    {
        "role": "MANAGER",
        "domain": "PAYRUN", 
        "action": "CREATE"
    }
    """
    try:
        role = request.data.get('role')
        domain = request.data.get('domain')
        action = request.data.get('action')
        
        if not all([role, domain, action]):
            return Response(
                {"error": "Missing required fields: role, domain, action"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        effective_permissions = permission_resolver.resolve_permissions()
        
        if role not in effective_permissions:
            return Response(
                {"error": f"Role '{role}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        has_permission = (
            effective_permissions[role].get(domain, {}).get(action, False)
        )
        
        response_data = {
            "has_permission": has_permission,
            "role": role,
            "domain": domain,
            "action": action,
            "effective": has_permission
        }
        
        # Log permission validation for security audit
        PermissionAuditLogger.log_permission_validation(
            request.user, role, domain, action, has_permission,
            client_ip=get_client_ip(request)
        )
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Permission validation error: {str(e)}")
        return Response(
            {"error": "Validation failed", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# URL Configuration
# accounts/api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('effective/', views.effective_permissions_api, name='api_permissions_effective'),
    path('effective/<str:role>/', views.effective_permissions_api, name='api_permissions_role'),
    path('validate/', views.validate_permission_api, name='api_permissions_validate'),
]