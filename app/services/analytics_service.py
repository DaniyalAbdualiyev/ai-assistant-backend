from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, text
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import uuid

from app.models.analytics import ConversationAnalytics, ClientAnalytics
from app.models.assistant import AIAssistant
from app.models.business_profile import BusinessProfile
from app.schemas.analytics import ConversationAnalyticsCreate, ClientAnalyticsCreate, ClientAnalyticsUpdate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsService:
    @staticmethod
    async def record_analytics_direct(db, assistant_id, business_profile_id, client_session_id=None, client_ip=None, client_device=None, message_count=None, response_time=None):
        """
        Record analytics data directly using SQL queries, bypassing ORM issues.
        This is a workaround for circular import problems.
        """
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            now = datetime.utcnow()
            
            if client_session_id:
                exists = db.execute(
                    text("SELECT id FROM client_analytics WHERE client_session_id = :session_id"),
                    {"session_id": client_session_id}
                ).fetchone()
                
                if not exists:
                    db.execute(
                        text("""
                        INSERT INTO client_analytics 
                        (client_session_id, assistant_id, business_profile_id, session_start, message_count, client_ip, client_device)
                        VALUES (:session_id, :assistant_id, :business_id, :start_time, 0, :client_ip, :client_device)
                        """),
                        {
                            "session_id": client_session_id,
                            "assistant_id": assistant_id,
                            "business_id": business_profile_id,
                            "start_time": now,
                            "client_ip": client_ip,
                            "client_device": client_device
                        }
                    )
                    
                    analytics_exists = db.execute(
                        text("""
                        SELECT id FROM conversation_analytics 
                        WHERE assistant_id = :assistant_id 
                        AND business_profile_id = :business_id 
                        AND date(date) = date(:today)
                        """),
                        {
                            "assistant_id": assistant_id,
                            "business_id": business_profile_id,
                            "today": today
                        }
                    ).fetchone()
                    
                    if analytics_exists:
                        db.execute(
                            text("""
                            UPDATE conversation_analytics 
                            SET total_conversations = total_conversations + 1,
                                last_updated = :updated_at
                            WHERE id = :id
                            """),
                            {
                                "updated_at": now,
                                "id": analytics_exists[0]
                            }
                        )
                    else:
                        db.execute(
                            text("""
                            INSERT INTO conversation_analytics 
                            (assistant_id, business_profile_id, total_conversations, total_messages, avg_response_time, date, last_updated)
                            VALUES (:assistant_id, :business_id, 1, 0, 0.0, :today, :updated_at)
                            """),
                            {
                                "assistant_id": assistant_id,
                                "business_id": business_profile_id,
                                "today": today,
                                "updated_at": now
                            }
                        )
            
            if message_count is not None or response_time is not None:
                if client_session_id:
                    client_data = db.execute(
                        text("SELECT id, message_count FROM client_analytics WHERE client_session_id = :session_id"),
                        {"session_id": client_session_id}
                    ).fetchone()
                    
                    if client_data:
                        client_id, current_message_count = client_data
                        
                        new_messages = 0
                        if message_count is not None:
                            new_messages = message_count - (current_message_count or 0)
                            
                            if new_messages > 0:
                                db.execute(
                                    text("UPDATE client_analytics SET message_count = :message_count WHERE id = :id"),
                                    {"message_count": message_count, "id": client_id}
                                )
                        
                        if response_time is not None:
                            db.execute(
                                text("UPDATE client_analytics SET avg_response_time = :response_time WHERE id = :id"),
                                {"response_time": response_time, "id": client_id}
                            )
                        
                        analytics_data = db.execute(
                            text("""
                            SELECT id, avg_response_time, total_messages 
                            FROM conversation_analytics 
                            WHERE assistant_id = :assistant_id 
                            AND business_profile_id = :business_id 
                            AND date(date) = date(:today)
                            """),
                            {
                                "assistant_id": assistant_id,
                                "business_id": business_profile_id,
                                "today": today
                            }
                        ).fetchone()
                        
                        if analytics_data:
                            analytics_id, current_avg_time, total_msgs = analytics_data
                            
                            if new_messages > 0:
                                db.execute(
                                    text("""
                                    UPDATE conversation_analytics 
                                    SET total_messages = total_messages + :new_messages,
                                        last_updated = :updated_at
                                    WHERE id = :id
                                    """),
                                    {
                                        "new_messages": new_messages,
                                        "updated_at": now,
                                        "id": analytics_id
                                    }
                                )
                            
                            if response_time is not None:
                                new_avg_time = response_time
                                if current_avg_time > 0 and total_msgs > 0:
                                    new_avg_time = ((current_avg_time * (total_msgs - 1)) + response_time) / total_msgs
                                
                                db.execute(
                                    text("""
                                    UPDATE conversation_analytics 
                                    SET avg_response_time = :response_time,
                                        last_updated = :updated_at
                                    WHERE id = :id
                                    """),
                                    {
                                        "response_time": new_avg_time,
                                        "updated_at": now,
                                        "id": analytics_id
                                    }
                                )
                        else:
                            db.execute(
                                text("""
                                INSERT INTO conversation_analytics 
                                (assistant_id, business_profile_id, total_conversations, total_messages, avg_response_time, date, last_updated)
                                VALUES (:assistant_id, :business_id, 1, :message_count, :response_time, :today, :updated_at)
                                """),
                                {
                                    "assistant_id": assistant_id,
                                    "business_id": business_profile_id,
                                    "message_count": new_messages,
                                    "response_time": response_time or 0.0,
                                    "today": today,
                                    "updated_at": now
                                }
                            )
                else:
                    analytics_data = db.execute(
                        text("""
                        SELECT id, avg_response_time, total_messages 
                        FROM conversation_analytics 
                        WHERE assistant_id = :assistant_id 
                        AND business_profile_id = :business_id 
                        AND date(date) = date(:today)
                        """),
                        {
                            "assistant_id": assistant_id,
                            "business_id": business_profile_id,
                            "today": today
                        }
                    ).fetchone()
                    
                    if analytics_data:
                        analytics_id, current_avg_time, total_msgs = analytics_data
                        
                        if message_count is not None:
                            db.execute(
                                text("""
                                UPDATE conversation_analytics 
                                SET total_messages = total_messages + :message_count,
                                    last_updated = :updated_at
                                WHERE id = :id
                                """),
                                {
                                    "message_count": message_count,
                                    "updated_at": now,
                                    "id": analytics_id
                                }
                            )
                        
                        if response_time is not None:
                            new_avg_time = response_time
                            if current_avg_time > 0 and total_msgs > 0:
                                new_avg_time = ((current_avg_time * (total_msgs - 1)) + response_time) / total_msgs
                            
                            db.execute(
                                text("""
                                UPDATE conversation_analytics 
                                SET avg_response_time = :response_time,
                                    last_updated = :updated_at
                                WHERE id = :id
                                """),
                                {
                                    "response_time": new_avg_time,
                                    "updated_at": now,
                                    "id": analytics_id
                                }
                            )
                    else:
                        db.execute(
                            text("""
                            INSERT INTO conversation_analytics 
                            (assistant_id, business_profile_id, total_conversations, total_messages, avg_response_time, date, last_updated)
                            VALUES (:assistant_id, :business_id, 0, :message_count, :response_time, :today, :updated_at)
                            """),
                            {
                                "assistant_id": assistant_id,
                                "business_id": business_profile_id,
                                "message_count": message_count or 0,
                                "response_time": response_time or 0.0,
                                "today": today,
                                "updated_at": now
                            }
                        )
            
            db.commit()
            return True
        except Exception as e:
            logger.error(f"Error recording analytics: {str(e)}")
            db.rollback()
            return False
    @staticmethod
    async def record_client_session(
        db: Session,
        client_session_id: str,
        assistant_id: int,
        business_profile_id: int,
        client_ip: Optional[str] = None,
        client_device: Optional[str] = None,
        client_location: Optional[str] = None
    ) -> Optional[ClientAnalytics]:
        """
        Record a new client session for analytics
        """
        try:
            client_analytics = ClientAnalytics(
                client_session_id=client_session_id,
                assistant_id=assistant_id,
                business_profile_id=business_profile_id,
                session_start=datetime.utcnow(),
                message_count=0,
                client_ip=client_ip,
                client_device=client_device,
                client_location=client_location
            )
            
            db.add(client_analytics)
            db.commit()
            db.refresh(client_analytics)
        except Exception as e:
            logger.error(f"Error creating client analytics record: {str(e)}")
            db.rollback()
            return None
        
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            result = db.execute(
                text("""
                SELECT id FROM conversation_analytics 
                WHERE assistant_id = :assistant_id 
                AND business_profile_id = :business_id 
                AND date(date) = date(:today)
                """),
                {
                    "assistant_id": assistant_id,
                    "business_id": business_profile_id,
                    "today": today
                }
            ).fetchone()
            
            if result:
                analytics_id = result[0]
                
                db.execute(
                    text("""
                    UPDATE conversation_analytics 
                    SET total_conversations = total_conversations + 1,
                        last_updated = :updated_at
                    WHERE id = :id
                    """),
                    {
                        "updated_at": datetime.utcnow(),
                        "id": analytics_id
                    }
                )
            else:
                db.execute(
                    text("""
                    INSERT INTO conversation_analytics 
                    (assistant_id, business_profile_id, total_conversations, total_messages, avg_response_time, date, last_updated)
                    VALUES (:assistant_id, :business_id, 1, 0, 0.0, :today, :updated_at)
                    """),
                    {
                        "assistant_id": assistant_id,
                        "business_id": business_profile_id,
                        "today": today,
                        "updated_at": datetime.utcnow()
                    }
                )
            
            db.commit()
            return client_analytics
        except Exception as e:
            logger.error(f"Error updating conversation analytics: {str(e)}")
            db.rollback()
            return client_analytics
    
    @staticmethod
    async def update_client_session(
        db: Session,
        client_session_id: str,
        update_data: ClientAnalyticsUpdate
    ) -> Optional[ClientAnalytics]:
        """
        Update an existing client session with new data
        """
        try:
            result = db.execute(
                text("SELECT id, assistant_id, business_profile_id, message_count FROM client_analytics WHERE client_session_id = :session_id"),
                {"session_id": client_session_id}
            ).fetchone()
            
            if not result:
                logger.warning(f"Client session not found: {client_session_id}")
                return None
                
            client_id, assistant_id, business_profile_id, current_message_count = result
        
            if update_data.session_end is not None:
                db.execute(
                    text("UPDATE client_analytics SET session_end = :session_end WHERE id = :id"),
                    {"session_end": update_data.session_end, "id": client_id}
                )
            
            if update_data.message_count is not None:
                new_messages = update_data.message_count - (current_message_count or 0)
                
                if new_messages > 0:
                    db.execute(
                        text("UPDATE client_analytics SET message_count = :message_count WHERE id = :id"),
                        {"message_count": update_data.message_count, "id": client_id}
                    )
                    
                    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    analytics_result = db.execute(
                        text("""
                        SELECT id FROM conversation_analytics 
                        WHERE assistant_id = :assistant_id 
                        AND business_profile_id = :business_id 
                        AND date(date) = date(:today)
                        """),
                        {
                            "assistant_id": assistant_id,
                            "business_id": business_profile_id,
                            "today": today
                        }
                    ).fetchone()
                    
                    if analytics_result:
                        analytics_id = analytics_result[0]
                        
                        db.execute(
                            text("""
                            UPDATE conversation_analytics 
                            SET total_messages = total_messages + :new_messages,
                                last_updated = :updated_at
                            WHERE id = :id
                            """),
                            {
                                "new_messages": new_messages,
                                "updated_at": datetime.utcnow(),
                                "id": analytics_id
                            }
                        )
                    else:
                        db.execute(
                            text("""
                            INSERT INTO conversation_analytics 
                            (assistant_id, business_profile_id, total_conversations, total_messages, avg_response_time, date, last_updated)
                            VALUES (:assistant_id, :business_id, 1, :messages, 0.0, :today, :updated_at)
                            """),
                            {
                                "assistant_id": assistant_id,
                                "business_id": business_profile_id,
                                "messages": new_messages,
                                "today": today,
                                "updated_at": datetime.utcnow()
                            }
                        )
        
            if update_data.avg_response_time is not None:
                db.execute(
                    text("UPDATE client_analytics SET avg_response_time = :response_time WHERE id = :id"),
                    {"response_time": update_data.avg_response_time, "id": client_id}
                )
                
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                
                analytics_result = db.execute(
                    text("""
                    SELECT id, avg_response_time, total_messages 
                    FROM conversation_analytics 
                    WHERE assistant_id = :assistant_id 
                    AND business_profile_id = :business_id 
                    AND date(date) = date(:today)
                    """),
                    {
                        "assistant_id": assistant_id,
                        "business_id": business_profile_id,
                        "today": today
                    }
                ).fetchone()
                
                if analytics_result:
                    analytics_id, current_avg_time, total_msgs = analytics_result
                    
                    new_avg_time = update_data.avg_response_time
                    if current_avg_time > 0 and total_msgs > 0:
                        new_avg_time = ((current_avg_time * (total_msgs - 1)) + update_data.avg_response_time) / total_msgs
                    
                    db.execute(
                        text("""
                        UPDATE conversation_analytics 
                        SET avg_response_time = :response_time,
                            last_updated = :updated_at
                        WHERE id = :id
                        """),
                        {
                            "response_time": new_avg_time,
                            "updated_at": datetime.utcnow(),
                            "id": analytics_id
                        }
                    )
                else:
                    db.execute(
                        text("""
                        INSERT INTO conversation_analytics 
                        (assistant_id, business_profile_id, total_conversations, total_messages, avg_response_time, date, last_updated)
                        VALUES (:assistant_id, :business_id, 1, 1, :response_time, :today, :updated_at)
                        """),
                        {
                            "assistant_id": assistant_id,
                            "business_id": business_profile_id,
                            "response_time": update_data.avg_response_time,
                            "today": today,
                            "updated_at": datetime.utcnow()
                        }
                    )
            
            db.commit()
            
            client_analytics = db.query(ClientAnalytics).filter(ClientAnalytics.id == client_id).first()
            return client_analytics
            
        except Exception as e:
            logger.error(f"Error updating client analytics: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    async def get_business_analytics_summary(
        db: Session,
        business_profile_id: int,
        days: int = 30
    ) -> Dict:
        """
        Get analytics summary for a business profile
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            result = db.execute(
                text("""
                SELECT id, total_conversations, total_messages, avg_response_time, date 
                FROM conversation_analytics 
                WHERE business_profile_id = :business_id 
                AND date >= :start_date 
                AND date <= :end_date 
                ORDER BY date
                """),
                {
                    "business_id": business_profile_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            analytics_records = result.fetchall()
        
            total_conversations = sum(record[1] for record in analytics_records) if analytics_records else 0
            total_messages = sum(record[2] for record in analytics_records) if analytics_records else 0
            
            avg_response_times = [record[3] for record in analytics_records if record[3] > 0]
            avg_response_time = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0
            
            avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0
            
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_result = db.execute(
                text("""
                SELECT total_conversations 
                FROM conversation_analytics 
                WHERE business_profile_id = :business_id 
                AND date(date) = date(:today)
                """),
                {
                    "business_id": business_profile_id,
                    "today": today
                }
            ).fetchone()
            
            active_conversations_today = today_result[0] if today_result else 0
        
            last_7_days = []
            last_7_days_messages = []
            
            for i in range(7):
                day = end_date - timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                
                day_result = db.execute(
                    text("""
                    SELECT total_conversations, total_messages 
                    FROM conversation_analytics 
                    WHERE business_profile_id = :business_id 
                    AND date(date) = date(:day_start)
                    """),
                    {
                        "business_id": business_profile_id,
                        "day_start": day_start
                    }
                ).fetchone()
                
                last_7_days.append(day_result[0] if day_result else 0)
                last_7_days_messages.append(day_result[1] if day_result else 0)
            
            last_7_days.reverse()
            last_7_days_messages.reverse()
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_response_time": avg_response_time,
                "avg_messages_per_conversation": avg_messages_per_conversation,
                "active_conversations_today": active_conversations_today,
                "conversations_last_7_days": last_7_days,
                "messages_last_7_days": last_7_days_messages
            }
        except Exception as e:
            logger.error(f"Error getting business analytics summary: {str(e)}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "avg_response_time": 0,
                "avg_messages_per_conversation": 0,
                "active_conversations_today": 0,
                "conversations_last_7_days": [0, 0, 0, 0, 0, 0, 0],
                "messages_last_7_days": [0, 0, 0, 0, 0, 0, 0]
            }
    
    @staticmethod
    async def get_assistant_analytics_summary(
        db: Session,
        assistant_id: int,
        days: int = 30
    ) -> Dict:
        """
        Get analytics summary for a specific assistant
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            result = db.execute(
                text("""
                SELECT id, total_conversations, total_messages, avg_response_time, date 
                FROM conversation_analytics 
                WHERE assistant_id = :assistant_id 
                AND date >= :start_date 
                AND date <= :end_date 
                ORDER BY date
                """),
                {
                    "assistant_id": assistant_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            analytics_records = result.fetchall()
            
            total_conversations = sum(record[1] for record in analytics_records) if analytics_records else 0
            total_messages = sum(record[2] for record in analytics_records) if analytics_records else 0
            
            avg_response_times = [record[3] for record in analytics_records if record[3] > 0]
            avg_response_time = sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0
            
            avg_messages_per_conversation = total_messages / total_conversations if total_conversations > 0 else 0
        
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_result = db.execute(
                text("""
                SELECT total_conversations 
                FROM conversation_analytics 
                WHERE assistant_id = :assistant_id 
                AND date(date) = date(:today)
                """),
                {
                    "assistant_id": assistant_id,
                    "today": today
                }
            ).fetchone()
            
            active_conversations_today = today_result[0] if today_result else 0
            
            last_7_days = []
            last_7_days_messages = []
            
            for i in range(7):
                day = end_date - timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                
                day_result = db.execute(
                    text("""
                    SELECT total_conversations, total_messages 
                    FROM conversation_analytics 
                    WHERE assistant_id = :assistant_id 
                    AND date(date) = date(:day_start)
                    """),
                    {
                        "assistant_id": assistant_id,
                        "day_start": day_start
                    }
                ).fetchone()
                
                last_7_days.append(day_result[0] if day_result else 0)
                last_7_days_messages.append(day_result[1] if day_result else 0)
            
            last_7_days.reverse()
            last_7_days_messages.reverse()
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "avg_response_time": avg_response_time,
                "avg_messages_per_conversation": avg_messages_per_conversation,
                "active_conversations_today": active_conversations_today,
                "conversations_last_7_days": last_7_days,
                "messages_last_7_days": last_7_days_messages
            }
        except Exception as e:
            logger.error(f"Error getting assistant analytics summary: {str(e)}")
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "avg_response_time": 0,
                "avg_messages_per_conversation": 0,
                "active_conversations_today": 0,
                "conversations_last_7_days": [0, 0, 0, 0, 0, 0, 0],
                "messages_last_7_days": [0, 0, 0, 0, 0, 0, 0]
            }
