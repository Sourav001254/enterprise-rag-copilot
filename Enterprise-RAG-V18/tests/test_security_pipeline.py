import pytest
from unittest.mock import patch, AsyncMock
from src.security.output_pipeline import OutputSecurityPipeline

@pytest.fixture
def output_pipeline():
    return OutputSecurityPipeline()

@pytest.mark.asyncio
async def test_output_pipeline_clean(output_pipeline):
    text = "Here is the summary of your pods."
    result = await output_pipeline.scan_output(text)
    assert result == text

@pytest.mark.asyncio
async def test_output_pipeline_redaction(output_pipeline):
    # Depending on the implementation, we test the exact output redaction.
    # Usually this mocks presidio or llm-guard.
    with patch.object(output_pipeline, "_redact_pii", new_callable=AsyncMock) as mock_redact:
        mock_redact.return_value = "Email: <REDACTED>"
        result = await output_pipeline.scan_output("Email: user@example.com")
        assert result == "Email: <REDACTED>"
        mock_redact.assert_called_once()
