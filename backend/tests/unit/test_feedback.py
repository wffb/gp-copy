import uuid
from datetime import datetime
from unittest.mock import Mock

from app.models.feedback import Feedback
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import FeedbackCreate
from app.services.feedback_service import FeedbackService


# repo layer
    # get top input by Fixture auto injection
def test_create_feedback_repository_success(test_db):

    # Arrange：prepare data
    repo = FeedbackRepository(test_db)
    feedback_data = FeedbackCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        message="Test message"
    )

    # Act
    result = repo.create(feedback_data)

    # Assert
    assert result is not None
    assert result.id is not None
    assert result.email == "john@example.com"

    # validate data exists in db
    db_record = test_db.query(Feedback).filter_by(id=result.id).first()
    assert db_record is not None

# service layer
def test_create_feedback_service_success():
    # Arrange：prepare mock db and db return
    mock_repo = Mock()
    expected_feedback = Feedback(
        id=uuid.uuid4(),
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        message="Test",
        created_at=datetime.utcnow()
    )

    # Configure Mock: Return the expected object when the create method is called.
    mock_repo.create.return_value = expected_feedback

    #Create Service and inject Mock
    service = FeedbackService(mock_repo)

    feedback_data = FeedbackCreate(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        message="Test"
    )
    # Act
    result = service.create_feedback(feedback_data)

    # Assert
    assert result == expected_feedback

    # assert that the create method was called with the expected data
    mock_repo.create.assert_called_once()
    mock_repo.create.assert_called_with(feedback_data)

# route layer
def test_create_feedback_route_success(client):
    # Arrange：prepare http json input
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "message": "Great app!"
    }

    # Act：send http request
    response = client.post("/api/v1/feedbacks/", json=payload)

    # Assert：validate response status code
    assert response.status_code == 200

    # validate response data
    data = response.json()
    assert "code" in data
    assert "data" in data
    assert data["code"] == 200