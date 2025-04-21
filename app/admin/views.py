from sqladmin import ModelView
from app.models.user import User
from app.models.assistant import AIAssistant
from app.models.business_profile import BusinessProfile
from app.models.analytics import ConversationAnalytics, ClientAnalytics
from app.models.message import Message
from app.models.user_subscription import UserSubscription
from app.models.subscription_plans import SubscriptionPlan


class UserAdmin(ModelView, model=User):
    name = "Users"
    icon = "fa-solid fa-users"
    category = "User Management"
    column_list = [User.id, User.name, User.email, User.created_at, User.is_admin]
    column_searchable_list = [User.name, User.email]
    column_sortable_list = [User.id, User.name, User.created_at]
    column_details_exclude_list = [User.password_hash]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    name_plural = "Users"


class AIAssistantAdmin(ModelView, model=AIAssistant):
    name = "AI Assistants"
    icon = "fa-solid fa-robot"
    category = "AI Management"
    column_list = [AIAssistant.id, AIAssistant.name, AIAssistant.model, AIAssistant.language, AIAssistant.created_at, AIAssistant.user_id]
    column_searchable_list = [AIAssistant.name, AIAssistant.model]
    column_sortable_list = [AIAssistant.id, AIAssistant.name, AIAssistant.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    name_plural = "AI Assistants"


class BusinessProfileAdmin(ModelView, model=BusinessProfile):
    name = "Business Profiles"
    icon = "fa-solid fa-building"
    category = "Business Management"
    column_list = [BusinessProfile.id, BusinessProfile.business_name, BusinessProfile.business_type, BusinessProfile.created_at, BusinessProfile.assistant_id]
    column_searchable_list = [BusinessProfile.business_name, BusinessProfile.business_type]
    column_sortable_list = [BusinessProfile.id, BusinessProfile.business_name, BusinessProfile.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    name_plural = "Business Profiles"


class ConversationAnalyticsAdmin(ModelView, model=ConversationAnalytics):
    name = "Conversation Analytics"
    icon = "fa-solid fa-chart-line"
    category = "Analytics"
    column_list = [
        ConversationAnalytics.id, 
        ConversationAnalytics.assistant_id, 
        ConversationAnalytics.business_profile_id, 
        ConversationAnalytics.total_conversations, 
        ConversationAnalytics.total_messages, 
        ConversationAnalytics.avg_response_time,
        ConversationAnalytics.date
    ]
    column_sortable_list = [
        ConversationAnalytics.id, 
        ConversationAnalytics.total_conversations, 
        ConversationAnalytics.total_messages, 
        ConversationAnalytics.date
    ]
    can_create = False  # Analytics should be created by the system
    can_edit = False
    can_delete = False
    can_view_details = True
    page_size = 25
    name_plural = "Conversation Analytics"


class ClientAnalyticsAdmin(ModelView, model=ClientAnalytics):
    name = "Client Analytics"
    icon = "fa-solid fa-users-viewfinder"
    category = "Analytics"
    column_list = [
        ClientAnalytics.id, 
        ClientAnalytics.client_session_id, 
        ClientAnalytics.assistant_id, 
        ClientAnalytics.business_profile_id, 
        ClientAnalytics.session_start, 
        ClientAnalytics.session_end, 
        ClientAnalytics.message_count
    ]
    column_sortable_list = [
        ClientAnalytics.id, 
        ClientAnalytics.session_start, 
        ClientAnalytics.message_count
    ]
    column_searchable_list = [ClientAnalytics.client_session_id]
    can_create = False  # Analytics should be created by the system
    can_edit = False
    can_delete = False
    can_view_details = True
    page_size = 25
    name_plural = "Client Analytics"


class MessageAdmin(ModelView, model=Message):
    name = "Messages"
    icon = "fa-solid fa-message"
    category = "Communication"
    column_list = [
        Message.id, 
        Message.user_query, 
        Message.ai_response, 
        Message.timestamp, 
        Message.user_id, 
        Message.assistant_id
    ]
    column_sortable_list = [Message.id, Message.timestamp]
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    page_size = 25
    name_plural = "Messages"


class SubscriptionPlanAdmin(ModelView, model=SubscriptionPlan):
    name = "Subscription Plans"
    icon = "fa-solid fa-credit-card"
    category = "Subscriptions"
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    name_plural = "Subscription Plans"


class UserSubscriptionAdmin(ModelView, model=UserSubscription):
    name = "User Subscriptions"
    icon = "fa-solid fa-receipt"
    category = "Subscriptions"
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    name_plural = "User Subscriptions"
