import os
from supabase import create_client, Client
from typing import Optional


class SupabaseClient:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            
            if not url or not key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
            
            cls._instance = create_client(url, key)
        return cls._instance

    @classmethod
    def store_analysis(cls, analysis_data: dict) -> dict:
        """Store bias analysis result in Supabase"""
        client = cls.get_client()
        
        # Insert into 'job_analyses' table
        result = client.table("job_analyses").insert(analysis_data).execute()
        return result.data[0] if result.data else {}
