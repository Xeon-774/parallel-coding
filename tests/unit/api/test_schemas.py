"""Unit tests for Job API schemas.

Tests Pydantic model validation and constraints for job submission and response.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from orchestrator.api.schemas import JobSubmitRequest, JobResponse
from orchestrator.core.db_models import JobStatus


# ======================= JobSubmitRequest Tests =======================


class TestJobSubmitRequestValidation:
    """Test JobSubmitRequest validation rules."""

    def test_valid_job_submit_request(self):
        """Test creating valid job submit request."""
        request = JobSubmitRequest(
            task_description="Build the project",
            worker_count=5,
        )

        assert request.task_description == "Build the project"
        assert request.worker_count == 5
        assert request.depth == 0  # default
        assert request.parent_job_id is None  # default

    def test_task_description_min_length(self):
        """Test task_description minimum length constraint."""
        with pytest.raises(ValidationError, match="at least 1 character"):
            JobSubmitRequest(
                task_description="",
                worker_count=1,
            )

    def test_task_description_max_length(self):
        """Test task_description maximum length constraint."""
        long_description = "x" * 4097  # Exceeds max_length=4096
        with pytest.raises(ValidationError, match="at most 4096 characters"):
            JobSubmitRequest(
                task_description=long_description,
                worker_count=1,
            )

    def test_task_description_at_max_length(self):
        """Test task_description at exactly max length (4096)."""
        max_description = "x" * 4096
        request = JobSubmitRequest(
            task_description=max_description,
            worker_count=1,
        )
        assert len(request.task_description) == 4096

    def test_worker_count_minimum(self):
        """Test worker_count minimum constraint (ge=1)."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            JobSubmitRequest(
                task_description="test",
                worker_count=0,
            )

    def test_worker_count_maximum(self):
        """Test worker_count maximum constraint (le=1000)."""
        with pytest.raises(ValidationError, match="less than or equal to 1000"):
            JobSubmitRequest(
                task_description="test",
                worker_count=1001,
            )

    def test_worker_count_valid_range(self):
        """Test worker_count valid range (1-1000)."""
        request1 = JobSubmitRequest(task_description="test", worker_count=1)
        request2 = JobSubmitRequest(task_description="test", worker_count=1000)

        assert request1.worker_count == 1
        assert request2.worker_count == 1000

    def test_depth_default_value(self):
        """Test depth has default value of 0."""
        request = JobSubmitRequest(
            task_description="test",
            worker_count=5,
        )
        assert request.depth == 0

    def test_depth_custom_value(self):
        """Test setting custom depth value."""
        request = JobSubmitRequest(
            task_description="test",
            worker_count=5,
            depth=3,
        )
        assert request.depth == 3

    def test_depth_minimum(self):
        """Test depth minimum constraint (ge=0)."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            JobSubmitRequest(
                task_description="test",
                worker_count=5,
                depth=-1,
            )

    def test_depth_maximum(self):
        """Test depth maximum constraint (le=1000)."""
        with pytest.raises(ValidationError, match="less than or equal to 1000"):
            JobSubmitRequest(
                task_description="test",
                worker_count=5,
                depth=1001,
            )

    def test_parent_job_id_default_none(self):
        """Test parent_job_id has default value of None."""
        request = JobSubmitRequest(
            task_description="test",
            worker_count=5,
        )
        assert request.parent_job_id is None

    def test_parent_job_id_custom_value(self):
        """Test setting custom parent_job_id."""
        request = JobSubmitRequest(
            task_description="test",
            worker_count=5,
            parent_job_id="parent-job-123",
        )
        assert request.parent_job_id == "parent-job-123"

    def test_all_fields_specified(self):
        """Test creating request with all fields specified."""
        request = JobSubmitRequest(
            task_description="Complex task",
            worker_count=10,
            depth=2,
            parent_job_id="parent-456",
        )

        assert request.task_description == "Complex task"
        assert request.worker_count == 10
        assert request.depth == 2
        assert request.parent_job_id == "parent-456"


# ======================= JobResponse Tests =======================


class TestJobResponseCreation:
    """Test JobResponse model creation."""

    def test_valid_job_response(self):
        """Test creating valid job response."""
        now = datetime.now()
        response = JobResponse(
            id="job-123",
            depth=0,
            worker_count=5,
            task_description="Build project",
            parent_job_id=None,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        assert response.id == "job-123"
        assert response.depth == 0
        assert response.worker_count == 5
        assert response.task_description == "Build project"
        assert response.parent_job_id is None
        assert response.status == JobStatus.PENDING
        assert response.created_at == now
        assert response.updated_at == now

    def test_job_response_with_parent(self):
        """Test job response with parent_job_id."""
        now = datetime.now()
        response = JobResponse(
            id="job-child",
            depth=1,
            worker_count=3,
            task_description="Subtask",
            parent_job_id="job-parent",
            status=JobStatus.RUNNING,
            created_at=now,
            updated_at=now,
        )

        assert response.parent_job_id == "job-parent"
        assert response.depth == 1

    def test_job_response_all_statuses(self):
        """Test job response with different JobStatus values."""
        now = datetime.now()

        for status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED]:
            response = JobResponse(
                id=f"job-{status.value}",
                depth=0,
                worker_count=1,
                task_description="test",
                parent_job_id=None,
                status=status,
                created_at=now,
                updated_at=now,
            )
            assert response.status == status

    def test_job_response_required_fields(self):
        """Test that all fields are required for JobResponse."""
        now = datetime.now()

        # Missing 'id' field
        with pytest.raises(ValidationError, match="Field required"):
            JobResponse(
                depth=0,
                worker_count=5,
                task_description="test",
                parent_job_id=None,
                status=JobStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

    def test_job_response_from_attributes_config(self):
        """Test that model_config allows from_attributes."""
        # Verify the config is set
        assert JobResponse.model_config.get("from_attributes") is True


class TestJobResponseSerialization:
    """Test JobResponse serialization."""

    def test_job_response_to_dict(self):
        """Test converting JobResponse to dict."""
        now = datetime.now()
        response = JobResponse(
            id="job-789",
            depth=2,
            worker_count=7,
            task_description="Complex task",
            parent_job_id="job-456",
            status=JobStatus.COMPLETED,
            created_at=now,
            updated_at=now,
        )

        response_dict = response.dict()

        assert response_dict["id"] == "job-789"
        assert response_dict["depth"] == 2
        assert response_dict["worker_count"] == 7
        assert response_dict["task_description"] == "Complex task"
        assert response_dict["parent_job_id"] == "job-456"
        assert response_dict["status"] == JobStatus.COMPLETED

    def test_job_response_to_json(self):
        """Test converting JobResponse to JSON."""
        now = datetime.now()
        response = JobResponse(
            id="job-json",
            depth=0,
            worker_count=1,
            task_description="JSON test",
            parent_job_id=None,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        json_str = response.json()

        assert "job-json" in json_str
        assert "JSON test" in json_str
        assert "pending" in json_str.lower()

    def test_job_response_json_round_trip(self):
        """Test JSON serialization round trip."""
        now = datetime.now()
        response1 = JobResponse(
            id="job-round-trip",
            depth=1,
            worker_count=3,
            task_description="Round trip test",
            parent_job_id="parent-xyz",
            status=JobStatus.RUNNING,
            created_at=now,
            updated_at=now,
        )

        # Serialize to JSON
        json_str = response1.json()

        # Deserialize back
        response2 = JobResponse.parse_raw(json_str)

        assert response2.id == response1.id
        assert response2.depth == response1.depth
        assert response2.worker_count == response1.worker_count
        assert response2.task_description == response1.task_description
        assert response2.parent_job_id == response1.parent_job_id
        assert response2.status == response1.status
