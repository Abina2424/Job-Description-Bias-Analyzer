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
                # Return None if credentials are not configured
                return None

            try:
                cls._instance = create_client(url, key)
            except (TypeError, Exception) as e:
                error_msg = str(e)
                if "proxy" in error_msg:
                    print("Supabase: Proxy configuration issue")
                elif "Invalid API key" in error_msg or "invalid" in error_msg.lower():
                    print("Supabase: Invalid API credentials - check SUPABASE_URL and SUPABASE_KEY")
                else:
                    print(f"Supabase: Connection failed - {error_msg}")
                return None
        return cls._instance

    @classmethod
    def store_analysis(cls, analysis_data: dict) -> dict:
        """Store bias analysis result in Supabase"""
        client = cls.get_client()

        if client is None:
            return {}  # Silently skip storage if not configured

        try:
            # Insert into 'job_analyses' table
            result = client.table("job_analyses").insert(analysis_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            error_msg = str(e)
            if "proxy" in error_msg:
                print("Supabase: Proxy configuration issue - check HTTP_PROXY/HTTPS_PROXY env vars")
            elif "connection" in error_msg.lower():
                print("Supabase: Connection failed - check URL and network")
            elif "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                print("Supabase: Authentication failed - check API key")
            else:
                print(f"Supabase insert failed: {error_msg}")
            return {}
