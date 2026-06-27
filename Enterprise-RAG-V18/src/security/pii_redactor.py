# src/security/pii_redactor.py
import logging
from typing import Tuple, List
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

logger = logging.getLogger(__name__)

class PIIRedactor:
    def __init__(self):
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logger.info("Presidio engines initialized.")
        except Exception as e:
            logger.error(f"Failed to init Presidio: {e}")
            self.analyzer = None
            self.anonymizer = None

    def redact(self, text: str) -> Tuple[str, List[str]]:
        if not self.analyzer or not self.anonymizer:
            return text, []
            
        try:
            # Entities to look for as specified
            entities = ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "IP_ADDRESS"]
            results = self.analyzer.analyze(text=text, entities=entities, language='en')
            
            anonymized_result = self.anonymizer.anonymize(text=text, analyzer_results=results)
            
            pii_found = [res.entity_type for res in results]
            
            return anonymized_result.text, pii_found
        except Exception as e:
            logger.error(f"Error redacting PII: {e}")
            return text, []

pii_redactor = PIIRedactor()
