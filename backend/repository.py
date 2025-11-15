from typing import List, Dict, Any
import logging
from .db_connector import connect_with_token

logger = logging.getLogger(__name__)

class AzureSqlRepository:
    def __init__(self):
        """Initialize with Microsoft Entra ID authenticated connection"""
        self.conn = connect_with_token()
        if not self.conn:
            raise Exception("Failed to establish database connection")
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query and return all rows as dictionaries."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"fetch_all error: {e}")
            raise
    
    def execute(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected row count."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            affected = cursor.rowcount
            self.conn.commit()
            
            cursor.close()
            return affected
        except Exception as e:
            logger.error(f"execute error: {e}")
            raise
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def fetch_recent_notifications(self):
        sql = """
            SELECT TOP 5
                Order_ID,
                Order_Date,
                Delivery_Time,
                'Delivery completed for order ' + CAST(Order_ID AS NVARCHAR(50)) AS Message
            FROM DeliveryLog
            WHERE Delivery_Time IS NOT NULL
            ORDER BY Order_Date DESC, Delivery_Time DESC;
        """
        return self.fetch_all(sql)


