"""
Usage tracking service module.

Logs and tracks AI API usage for monitoring and analytics.

TODO: Add cost calculation (tokens × cost_per_token)
TODO: Add usage alerts/quotas
TODO: Add historical analytics and trends
"""

from models import db, UsageLog
import logging

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Tracks and logs AI API usage.
    
    TODO: Add batch logging for performance
    TODO: Add export to CSV/JSON for analysis
    """
    
    @staticmethod
    def log_usage(
        model_name: str,
        tokens_input: int,
        tokens_output: int,
        request_type: str = "chat"
    ) -> UsageLog:
        """
        Log a single API usage event.
        
        Args:
            model_name (str): Model used (e.g., 'gemini-pro')
            tokens_input (int): Tokens in input/prompt
            tokens_output (int): Tokens in output/response
            request_type (str): Type of request (chat, generate, embed, review, etc.)
            
        Returns:
            UsageLog: Created usage log entry
            
        TODO: Add validation of token counts
        TODO: Add error handling
        """
        try:
            log_entry = UsageLog(
                model_name=model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                request_type=request_type,
                request_count=1
            )
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info(
                f"Logged usage: {model_name} | "
                f"{request_type} | "
                f"In: {tokens_input}, Out: {tokens_output}"
            )
            return log_entry
        
        except Exception as e:
            logger.error(f"Error logging usage: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_total_usage() -> dict:
        """
        Get aggregated usage statistics across all requests.
        
        Returns:
            dict: Dictionary with total_requests, total_tokens_input, total_tokens_output, etc.
            
        TODO: Add time-based filtering (today, this week, etc.)
        TODO: Add per-model breakdown
        TODO: Add per-request-type breakdown
        """
        try:
            from sqlalchemy import func
            
            result = db.session.query(
                func.count(UsageLog.id).label('total_requests'),
                func.sum(UsageLog.tokens_input).label('total_tokens_input'),
                func.sum(UsageLog.tokens_output).label('total_tokens_output'),
            ).first()
            
            total_input = result.total_tokens_input or 0
            total_output = result.total_tokens_output or 0
            
            return {
                'total_requests': result.total_requests or 0,
                'total_tokens_input': total_input,
                'total_tokens_output': total_output,
                'total_tokens': total_input + total_output,
                'avg_tokens_per_request': (total_input + total_output) // max(result.total_requests, 1)
            }
        
        except Exception as e:
            logger.error(f"Error getting usage stats: {str(e)}")
            return {
                'total_requests': 0,
                'total_tokens_input': 0,
                'total_tokens_output': 0,
                'total_tokens': 0,
                'avg_tokens_per_request': 0
            }
    
    @staticmethod
    def get_recent_usage(limit: int = 10) -> list:
        """
        Get recent usage entries.
        
        Args:
            limit (int): Maximum number of entries to return
            
        Returns:
            list: Recent UsageLog entries
            
        TODO: Add filtering options (time range, model, request type)
        """
        try:
            logs = UsageLog.query.order_by(UsageLog.created_at.desc()).limit(limit).all()
            return logs
        except Exception as e:
            logger.error(f"Error getting recent usage: {str(e)}")
            return []
    
    @staticmethod
    def get_usage_by_model() -> dict:
        """
        Get usage breakdown by model.
        
        Returns:
            dict: Model names as keys, usage stats as values
            
        TODO: Add this query
        """
        pass
    
    @staticmethod
    def get_usage_by_request_type() -> dict:
        """
        Get usage breakdown by request type (chat, generate, embed, etc.).
        
        Returns:
            dict: Request types as keys, usage stats as values
            
        PHASE 2 TODO: Add this query
        """
        pass
