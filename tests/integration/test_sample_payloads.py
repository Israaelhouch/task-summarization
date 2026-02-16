import json
from pathlib import Path

from app.services.summarization_service import SummarizationService
from app.models.request_models import TaskSummarizeRequest


def test_sample_payloads_generate_summary():
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "sample_payloads.json"
    payloads = json.loads(fixture_path.read_text())
    svc = SummarizationService()

    assert isinstance(payloads, list)
    assert len(payloads) >= 1

    for payload in payloads:
        req = TaskSummarizeRequest(**payload)
        res = svc.summarize(req)
        assert isinstance(res.summary, str)
        assert res.summary.strip()
        assert "This task" in res.summary
