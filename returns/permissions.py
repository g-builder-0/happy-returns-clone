from rest_framework import permissions


class IsMerchantOwner(permissions.BasePermission):
    """
    Custom permission to only allow users to access data for their own merchant.
    Prevents cross-merchant data access and ensures multi-tenant isolation.
    """

    def has_permission(self, request, view):
        """
        Check if user has permission to access this endpoint at all.
        Called before the view is executed.
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # User must have a profile
        if not hasattr(request.user, 'profile'):
            return False

        # User must have a merchant (not applicable for consumers)
        if not request.user.profile.merchant:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access THIS specific object.
        Called when accessing a specific return, refund, etc.
        """
        # Object must have a merchant attribute
        if not hasattr(obj, 'merchant'):
            return False

        # Check if object's merchant matches user's merchant
        return obj.merchant == request.user.profile.merchant


class IsConsumerOwner(permissions.BasePermission):
    """
    Custom permission to only allow consumers to access their own returns.
    Prevents consumers from seeing other consumers' returns.
    """

    def has_permission(self, request, view):
        """
        Check if user is authenticated and is a consumer.
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # User must have a profile
        if not hasattr(request.user, 'profile'):
            return False

        # User must be a consumer (not merchant staff)
        if request.user.profile.role != 'CONSUMER':
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """
        Check if the return belongs to this consumer.
        """
        # For Return objects, check consumer field
        if hasattr(obj, 'consumer'):
            return obj.consumer == request.user.profile

        return False


class IsReturnBarStaff(permissions.BasePermission):
    """
    Custom permission to only allow return bar staff to perform
    return bar operations (assessments, drop-off confirmations).
    """

    def has_permission(self, request, view):
        """
        Check if user is authenticated and is return bar staff.
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False

        # User must have a profile
        if not hasattr(request.user, 'profile'):
            return False

        # User must be return bar staff
        if request.user.profile.role != 'RETURN_BAR_STAFF':
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """
        Return bar staff can access any object (no additional restrictions).
        They need to process returns from all merchants.
        """
        return True
