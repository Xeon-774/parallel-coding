"""
Tests for Recursive Orchestration Utilities
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from orchestrator.core.recursive_utils import (
    RecursiveWorkspaceManager,
    calculate_child_depth,
    get_ancestry_chain,
    is_recursive_worker,
    validate_recursion_depth,
)


class TestRecursiveWorkspaceManager:
    """Test RecursiveWorkspaceManager class"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def manager(self, temp_workspace):
        """Create workspace manager instance"""
        return RecursiveWorkspaceManager(job_id="test_job_123", workspace_root=temp_workspace)

    def test_create_depth_directory(self, manager):
        """Test creating depth directory"""
        depth_dir = manager.create_depth_directory(0)

        assert depth_dir.exists()
        assert depth_dir.name == "depth_0"
        assert (depth_dir / "metadata.json").exists()

    def test_create_worker_directory(self, manager):
        """Test creating worker directory"""
        manager.create_depth_directory(0)
        worker_dir = manager.create_worker_directory(0, "worker_1", is_recursive=False)

        assert worker_dir.exists()
        assert worker_dir.name == "worker_1"
        assert (worker_dir / "input.txt").exists()
        assert (worker_dir / "output.txt").exists()
        assert (worker_dir / "result.json").exists()

    def test_create_recursive_worker_directory(self, manager):
        """Test creating recursive worker directory"""
        manager.create_depth_directory(0)
        worker_dir = manager.create_worker_directory(0, "worker_2", is_recursive=True)

        assert worker_dir.exists()
        assert worker_dir.name == "worker_2_recursive"
        assert (worker_dir / "recursive_call.json").exists()
        assert (worker_dir / "child_job_ref.json").exists()

    def test_write_and_read_depth_metadata(self, manager):
        """Test writing and reading metadata"""
        manager.create_depth_directory(0)

        metadata = {"workers_count": 3, "recursive_workers": ["worker_2"]}

        manager.write_depth_metadata(0, metadata)
        read_metadata = manager.read_depth_metadata(0)

        assert read_metadata is not None
        assert read_metadata["depth"] == 0
        assert read_metadata["job_id"] == "test_job_123"
        assert read_metadata["workers_count"] == 3
        assert "created_at" in read_metadata

    def test_write_parent_info(self, manager):
        """Test writing parent information"""
        manager.create_depth_directory(1)
        manager.write_parent_info(1, "parent_job", "worker_2", 0)

        parent_info_file = manager.get_depth_directory(1) / "parent_info.json"
        assert parent_info_file.exists()

        with open(parent_info_file, "r") as f:
            parent_info = json.load(f)

        assert parent_info["parent_job_id"] == "parent_job"
        assert parent_info["parent_worker_id"] == "worker_2"
        assert parent_info["parent_depth"] == 0
        assert parent_info["child_depth"] == 1

    def test_write_recursive_call_info(self, manager):
        """Test writing recursive call information"""
        manager.create_depth_directory(0)
        manager.create_worker_directory(0, "worker_2", is_recursive=True)

        request_payload = {"request": "Child task", "config": {"max_workers": 3}}

        manager.write_recursive_call_info(
            depth=0,
            worker_id="worker_2",
            child_job_id="child_123",
            child_depth=1,
            request_payload=request_payload,
        )

        recursive_file = (
            manager.get_depth_directory(0) / "worker_2_recursive" / "recursive_call.json"
        )

        assert recursive_file.exists()

        with open(recursive_file, "r") as f:
            recursive_info = json.load(f)

        assert recursive_info["worker_id"] == "worker_2"
        assert recursive_info["child_job_id"] == "child_123"
        assert recursive_info["child_depth"] == 1
        assert recursive_info["request_payload"] == request_payload

    def test_create_logs_directory(self, manager):
        """Test creating logs directory"""
        logs_dir = manager.create_logs_directory()

        assert logs_dir.exists()
        assert logs_dir.name == "logs"

    def test_create_reports_directory(self, manager):
        """Test creating reports directory"""
        reports_dir = manager.create_reports_directory()

        assert reports_dir.exists()
        assert reports_dir.name == "reports"

    def test_write_job_metadata(self, manager):
        """Test writing job metadata"""
        metadata = {"user_request": "Test task", "max_depth": 2, "total_workers": 5}

        manager.write_job_metadata(metadata)

        metadata_file = manager.job_dir / "job_metadata.json"
        assert metadata_file.exists()

        with open(metadata_file, "r") as f:
            job_metadata = json.load(f)

        assert job_metadata["job_id"] == "test_job_123"
        assert job_metadata["user_request"] == "Test task"
        assert "created_at" in job_metadata
        assert "workspace_path" in job_metadata

    def test_get_all_depths(self, manager):
        """Test getting all depth levels"""
        # Create multiple depths
        manager.create_depth_directory(0)
        manager.create_depth_directory(1)
        manager.create_depth_directory(2)

        depths = manager.get_all_depths()

        assert depths == [0, 1, 2]

    def test_build_recursion_tree(self, manager):
        """Test building recursion tree"""
        # Create depth 0
        manager.create_depth_directory(0)
        manager.write_depth_metadata(0, {"workers_count": 2})
        manager.create_worker_directory(0, "worker_1", is_recursive=False)
        manager.create_worker_directory(0, "worker_2", is_recursive=True)

        # Create depth 1
        manager.create_depth_directory(1)
        manager.write_parent_info(1, "test_job_123", "worker_2", 0)
        manager.write_depth_metadata(1, {"workers_count": 3})

        # Build tree
        tree = manager.build_recursion_tree()

        assert tree["job_id"] == "test_job_123"
        assert "depth_0" in tree["depths"]
        assert "depth_1" in tree["depths"]

        depth_0 = tree["depths"]["depth_0"]
        assert depth_0["depth"] == 0
        assert len(depth_0["workers"]) == 2

        depth_1 = tree["depths"]["depth_1"]
        assert depth_1["depth"] == 1
        assert "parent_info" in depth_1


class TestUtilityFunctions:
    """Test utility functions"""

    def test_validate_recursion_depth_success(self):
        """Test recursion depth validation - success"""
        # Should not raise
        validate_recursion_depth(0, 3)
        validate_recursion_depth(2, 3)

    def test_validate_recursion_depth_failure(self):
        """Test recursion depth validation - failure"""
        with pytest.raises(ValueError, match="Maximum recursion depth"):
            validate_recursion_depth(3, 3)

        with pytest.raises(ValueError, match="Maximum recursion depth"):
            validate_recursion_depth(5, 3)

    def test_calculate_child_depth(self):
        """Test calculating child depth"""
        assert calculate_child_depth(0) == 1
        assert calculate_child_depth(1) == 2
        assert calculate_child_depth(5) == 6

    def test_is_recursive_worker(self, tmp_path):
        """Test checking if worker is recursive"""
        # Create recursive worker directory
        recursive_worker = tmp_path / "worker_2_recursive"
        recursive_worker.mkdir()
        (recursive_worker / "recursive_call.json").touch()

        # Create normal worker directory
        normal_worker = tmp_path / "worker_1"
        normal_worker.mkdir()

        assert is_recursive_worker(recursive_worker) is True
        assert is_recursive_worker(normal_worker) is False

    def test_get_ancestry_chain_root(self):
        """Test ancestry chain for root job"""
        chain = get_ancestry_chain("job_123")

        assert chain == ["Job job_123"]

    def test_get_ancestry_chain_child(self):
        """Test ancestry chain for child job"""
        chain = get_ancestry_chain(
            job_id="job_456", parent_job_id="job_123", parent_worker_id="worker_2"
        )

        assert chain == ["Job job_123 > worker_2", "Job job_456"]


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_two_level_recursion_structure(self, temp_workspace):
        """Test creating a two - level recursion structure"""
        # Create root job
        root_manager = RecursiveWorkspaceManager("root_job", temp_workspace)

        # Depth 0
        root_manager.create_depth_directory(0)
        root_manager.write_depth_metadata(0, {"workers_count": 3})

        # Create workers at depth 0
        root_manager.create_worker_directory(0, "worker_1", is_recursive=False)
        root_manager.create_worker_directory(0, "worker_2", is_recursive=True)
        root_manager.create_worker_directory(0, "worker_3", is_recursive=False)

        # Worker 2 spawns recursion
        root_manager.create_depth_directory(1)
        root_manager.write_parent_info(1, "root_job", "worker_2", 0)
        root_manager.write_recursive_call_info(
            depth=0,
            worker_id="worker_2",
            child_job_id="child_job",
            child_depth=1,
            request_payload={"request": "Sub - tasks", "config": {}},
        )

        # Depth 1 workers
        root_manager.write_depth_metadata(1, {"workers_count": 2})
        root_manager.create_worker_directory(1, "worker_1_1", is_recursive=False)
        root_manager.create_worker_directory(1, "worker_1_2", is_recursive=False)

        # Create logs and reports
        root_manager.create_logs_directory()
        root_manager.create_reports_directory()

        # Write job metadata
        root_manager.write_job_metadata(
            {"user_request": "Complex task", "max_recursion_depth": 2, "actual_recursion_depth": 1}
        )

        # Verify structure
        job_dir = temp_workspace / "job_root_job"
        assert (job_dir / "depth_0").exists()
        assert (job_dir / "depth_1").exists()
        assert (job_dir / "logs").exists()
        assert (job_dir / "reports").exists()
        assert (job_dir / "job_metadata.json").exists()

        # Verify depth 0 workers
        assert (job_dir / "depth_0" / "worker_1").exists()
        assert (job_dir / "depth_0" / "worker_2_recursive").exists()
        assert (job_dir / "depth_0" / "worker_3").exists()

        # Verify depth 1 workers
        assert (job_dir / "depth_1" / "worker_1_1").exists()
        assert (job_dir / "depth_1" / "worker_1_2").exists()

        # Verify recursion tree
        tree = root_manager.build_recursion_tree()
        assert len(tree["depths"]) == 2
        assert tree["depths"]["depth_1"]["parent_info"]["parent_job_id"] == "root_job"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
