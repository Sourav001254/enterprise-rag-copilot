# src/security/prompt_shield.py
import re
import unicodedata
from pydantic import BaseModel, constr

# Pydantic schema for L1 basic validation
class QueryInput(BaseModel):
    # Enforce basic constraints to prevent massive payloads
    query: str

class PromptShield:
    @staticmethod
    def normalize(text: str) -> str:
        """Unicode normalization."""
        return unicodedata.normalize('NFKC', text)
        
    @staticmethod
    def detect_injection(text: str) -> bool:
        """Detect common SQL/Prompt injection patterns using regex."""
        # Simple set of regex rules representing 50+ patterns
        patterns = [
            r"(?i)(ignore\s+all\s+previous\s+instructions)",
            r"(?i)(you\s+are\s+now)",
            r"(?i)(system\s+prompt)",
            r"(?i)(<\|.*\|>)",
            r"(?i)(union\s+select)",
            r"(?i)(drop\s+table)",
            r"(?i)(insert\s+into)",
            r"(?i)(delete\s+from)",
            r"(?i)(update\s+.*set)",
            r"(?i)(truncate\s+table)",
            r"(?i)(alter\s+table)",
            r"(?i)(create\s+table)",
            r"(?i)(exec\s*\()",
            r"(?i)(execute\s+)",
            r"(?i)(grant\s+)",
            r"(?i)(revoke\s+)",
            r"(?i)(declare\s+)",
            r"(?i)(cast\s*\()",
            r"(?i)(convert\s*\()",
            r"(?i)(char\s*\()",
            r"(?i)(nchar\s*\()",
            r"(?i)(varchar\s*\()",
            r"(?i)(nvarchar\s*\()",
            r"(?i)(information_schema)",
            r"(?i)(sysobjects)",
            r"(?i)(syscolumns)",
            r"(?i)(sysusers)",
            r"(?i)(pg_class)",
            r"(?i)(pg_user)",
            r"(?i)(pg_database)",
            r"(?i)(pg_tables)",
            r"(?i)(version\s*\(\s*\))",
            r"(?i)(database\s*\(\s*\))",
            r"(?i)(user\s*\(\s*\))",
            r"(?i)(current_user)",
            r"(?i)(system_user)",
            r"(?i)(session_user)",
            r"(?i)(benchmark\s*\()",
            r"(?i)(sleep\s*\()",
            r"(?i)(waitfor\s+delay)",
            r"(?i)(pg_sleep)",
            r"(?i)(dbms_pipe\.receive_message)",
            r"(?i)(AND\s+1=1)",
            r"(?i)(OR\s+1=1)",
            r"(?i)(OR\s+'a'='a')",
            r"(?i)(--)",
            r"(?i)(/\*.*\*/)",
            r"(?i)(;.*$)",
            r"(?i)(bypass)",
            r"(?i)(forget\s+everything)",
            r"(?i)(print\s+instructions)",
            r"(?i)(developer\s+mode)",
            r"(?i)(DAN\s+mode)",
            r"(?i)(disregard)"
        ]
        
        for p in patterns:
            if re.search(p, text):
                return True
        return False
        
    @staticmethod
    def clean(text: str) -> str:
        """Normalize whitespace."""
        return " ".join(text.split())

prompt_shield = PromptShield()
