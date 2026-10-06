from .models import Message

def unread_notifications(request):
    """
    Returns unread notification metrics for the authenticated student.
    Used by the sidebar bell icon to show/hide the blue dot indicator.
    """
    if not request.user.is_authenticated:
        return {
            'has_unread_notifications': False,
            'unread_notifications_count': 0,
        }
    try:
        unread_count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(
            sender=request.user,
        ).exclude(
            hidden_for=request.user,
        ).exclude(
            conversation__hidden_for=request.user,
        ).count()
        return {
            'has_unread_notifications': unread_count > 0,
            'unread_notifications_count': unread_count,
        }
    except Exception:
        return {
            'has_unread_notifications': False,
            'unread_notifications_count': 0,
        }
