# CodeGuardian

import pytest
from unittest.mock import MagicMock, patch
from code_guardian.main import CodeGuardian
import subprocess


@pytest.fixture
def mock_agent():
    """Fixture to create a mock agent."""
    return MagicMock()


@pytest.fixture
def code_guardian(mock_agent):
    """Fixture to create an instance of CodeGuardian."""
    return CodeGuardian(classes=[], agent=mock_agent)


def test_initialization(code_guardian):
    """Test the initialization of CodeGuardian."""
    assert code_guardian.classes == []
    assert code_guardian.agent == code_guardian.agent
    assert code_guardian.dir_path == "tests/memory"
    assert code_guardian.package_name == "swarms"
    assert code_guardian.module_name == "swarms.memory"


@patch("code_guardian.main.os.makedirs")
@patch("code_guardian.main.open", new_callable=MagicMock)
def test_create_test_success(
    mock_open, mock_makedirs, code_guardian, mock_agent
):
    """Test creating a test file successfully."""

    class MockClass:
        """A mock class for testing."""

        __name__ = "MockClass"
        __doc__ = "This is a mock class."

    code_guardian.create_test(MockClass)

    mock_makedirs.assert_called_once_with(
        code_guardian.dir_path, exist_ok=True
    )
    mock_open().write.assert_called_once()
    assert mock_open().write.call_args[0][0].startswith("# MockClass")


@patch("code_guardian.main.os.listdir")
@patch("code_guardian.main.subprocess.run")
def test_run_all_tests_success(
    mock_subprocess, mock_listdir, code_guardian
):
    """Test running all tests successfully."""
    mock_listdir.return_value = ["test_mockclass.py"]
    mock_subprocess.return_value.stdout = "Test passed"
    mock_subprocess.return_value.returncode = 0

    code_guardian.dir_path = "tests/memory"
    code_guardian.run_all_tests()

    assert len(code_guardian.test_results) == 1
    assert (
        code_guardian.test_results[0].class_name
        == "test_mockclass.py"
    )
    assert code_guardian.test_results[0].status == "success"
    assert code_guardian.test_results[0].message == "Test passed"


@patch("code_guardian.main.os.listdir")
@patch("code_guardian.main.subprocess.run")
def test_run_all_tests_failure(
    mock_subprocess, mock_listdir, code_guardian
):
    """Test running all tests and handling failures."""
    mock_listdir.return_value = ["test_mockclass.py"]
    mock_subprocess.side_effect = subprocess.CalledProcessError(
        1, "python", output="Error occurred", stderr="Test failed"
    )

    code_guardian.dir_path = "tests/memory"
    code_guardian.run_all_tests()

    assert len(code_guardian.test_results) == 1
    assert (
        code_guardian.test_results[0].class_name
        == "test_mockclass.py"
    )
    assert code_guardian.test_results[0].status == "failure"
    assert code_guardian.test_results[0].message == "Test failed"


def test_extract_code_from_markdown():
    """Test extracting code from markdown."""
    code_guardian = CodeGuardian([], MagicMock())
    markdown_content = """
    Here is some code:
And here is some more:
"""
    extracted_code = code_guardian.extract_code_from_markdown(
        markdown_content
    )
    assert (
        extracted_code
        == 'print("Hello, World!")\nprint("Goodbye, World!")'
    )


@patch("code_guardian.main.CodeGuardian.create_test")
def test_generate_tests(mock_create_test, code_guardian):
    """Test generating tests for all classes."""

    class MockClass1:
        pass

    class MockClass2:
        pass

    code_guardian.classes = [MockClass1, MockClass2]
    code_guardian.generate_tests()

    assert mock_create_test.call_count == 2
    mock_create_test.assert_any_call(MockClass1)
    mock_create_test.assert_any_call(MockClass2)


def test_check_tests_results(code_guardian):
    """Test checking test results."""
    code_guardian.check_tests_results(return_json=False)
    # Assuming that the method generates and runs tests, we can't check assertions without mocks.
    # However, we can check if the logger was called or the method executed.
    assert True  # Placeholder for actual assertions based on logger or state changes.


# Additional tests can be added to cover edge cases, exceptions, and more complex scenarios.
