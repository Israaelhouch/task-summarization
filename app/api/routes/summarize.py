from fastapi import APIRouter, Query

from app.models.request_models import TaskSummarizeRequest
from app.models.response_models import TaskSummarizeResponse
from app.services.summarization_service import SummarizationService  # adjust import path if different

router = APIRouter(prefix="/summarize", tags=["summarize"])
service = SummarizationService()


@router.post("", response_model=TaskSummarizeResponse)
def summarize(
    req: TaskSummarizeRequest,
    include_events: bool = Query(False, description="Return normalized events in the response"),
):
    return service.summarize(req, include_events=include_events)
