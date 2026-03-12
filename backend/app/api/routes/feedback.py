from fastapi import APIRouter, Depends, status

from app.schemas import SuccessResponse
from app.schemas.feedback import FeedbackCreateRequest, FeedbackCreate
from app.services.feedback_service import FeedbackService, get_feedback_service


router = APIRouter()


@router.post("/", status_code=status.HTTP_200_OK)
def create_feedback(
        request: FeedbackCreateRequest,
        service: FeedbackService = Depends(get_feedback_service)
):
    """
    Create a feedback from user or unlogged-in visitors.

    - **first_name**: First name of the person
    - **last_name**: Last name of the person
    - **email**: Email address of the person
    - **message**: Feedback message
    """
    feedback_create = FeedbackCreate(**request.model_dump())
    service.create_feedback(feedback_create)

    return SuccessResponse(code=200,data="Feedback created successfully")