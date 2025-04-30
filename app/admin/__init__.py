from sqladmin import Admin
from app.database import engine
from app.admin.views import (
    UserAdmin, 
    AIAssistantAdmin, 
    BusinessProfileAdmin, 
    ConversationAnalyticsAdmin,
    MessageAdmin,
    SubscriptionPlanAdmin,
    UserSubscriptionAdmin
)

def setup_admin(app):
    """
    Setup SQLAdmin for the FastAPI application
    """
    # Create Admin instance
    admin = Admin(app, engine)
    
    # Add model views
    admin.add_view(UserAdmin)
    admin.add_view(AIAssistantAdmin)
    admin.add_view(BusinessProfileAdmin)
    admin.add_view(ConversationAnalyticsAdmin)
    admin.add_view(MessageAdmin)
    admin.add_view(SubscriptionPlanAdmin)
    admin.add_view(UserSubscriptionAdmin)
    
    return admin
