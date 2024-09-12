import time
import inspect
import os
import re
import subprocess
import threading
from typing import Any, List

from loguru import logger
from pydantic import BaseModel, Field
from swarms.prompts.tests import TEST_WRITER_SOP_PROMPT
from swarms import Agent


# Pydantic model for metadata
class TestResult(BaseModel):
    class_name: str
    class_docstring: str
    class_source_code: str
    test_file_path: str
    test_file_content: str
    status: str  # "success" or "failure"
    message: str  # Detailed message


class CodeGuardianLog(BaseModel):
    tests: List[TestResult]
    timestamp: str = Field(
        time.strftime("%Y-%m-%d %H:%M:%S"),
        description="Timestamp of the log",
    )


class CodeGuardian:
    """
    Initialize CodeGuardian with the provided classes, agent, and directory path.

    Args:
        classes (List[Any]): A list of classes for which tests will be generated.
        agent (OpenAIChat): The agent responsible for generating tests using the OpenAIChat model.
        dir_path (str): The directory where generated tests will be saved. Defaults to "tests/memory".
    """

    def __init__(
        self,
        classes: List[Any],
        agent: Agent,
        dir_path: str = "tests/memory",
        package_name: str = "swarms",
        module_name: str = "swarms.memory",
    ):
        self.classes = classes
        self.agent = agent
        self.dir_path = dir_path
        self.package_name = package_name
        self.module_name = module_name
        # self.test_results: List[TestResult] = []

        # Set up the logger
        logger.add(
            "code_guardian.log",
            format="{time} {level} {message}",
            level="DEBUG",
        )
        logger.info("CodeGuardian initialized.")

        # Log
        self.log = CodeGuardianLog(
            tests=[],
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def extract_code_from_markdown(
        self, markdown_content: str
    ) -> str:
        """
        Extracts code blocks from a Markdown string and returns them as a single string.

        Args:
            markdown_content (str): The Markdown content as a string.

        Returns:
            str: A single string containing all the code blocks separated by newlines.
        """
        pattern = r"```(?:\w+\n)?(.*?)```"
        matches = re.findall(pattern, markdown_content, re.DOTALL)
        return "\n".join(code.strip() for code in matches)

    def create_test(self, cls: Any):
        """
        Processes the class's docstring and source code to create test files.

        Args:
            cls (Any): The class to generate tests for.
        """
        doc = inspect.getdoc(cls)
        source = inspect.getsource(cls)
        input_content = f"Class Name: {cls.__name__}\n\nDocumentation:\n{doc}\n\nSource Code:\n{source}"

        logger.debug(
            f"Generating tests for class {cls.__name__} using agent."
        )

        try:
            processed_content = self.agent.run(
                TEST_WRITER_SOP_PROMPT(
                    input_content, self.package_name, self.module_name
                )
            )
            processed_content = self.extract_code_from_markdown(
                processed_content
            )

            doc_content = f"# {cls.__name__}\n\n{processed_content}\n"
            os.makedirs(self.dir_path, exist_ok=True)

            file_path = os.path.join(
                self.dir_path, f"{cls.__name__.lower()}.py"
            )
            with open(file_path, "w") as file:
                file.write(doc_content)

            self.log.tests.append(
                TestResult(
                    class_name=cls.__name__,
                    class_docstring=doc,
                    class_source_code=source,
                    test_file_path=file_path,
                    test_file_content=doc_content,
                    status="success",
                    message="Test file created successfully",
                )
            )

            logger.info(
                f"Test file for {cls.__name__} created at {file_path}"
            )
        except Exception as e:
            logger.error(
                f"Error while creating test for class {cls.__name__}: {e}"
            )

    def generate_tests(self):
        """
        Generates test files for all classes in a multi-threaded manner.
        """
        threads = []
        logger.info("Starting test generation for all classes.")
        for cls in self.classes:
            thread = threading.Thread(
                target=self.create_test, args=(cls,)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        logger.info("Test generation completed.")

    def run_all_tests(
        self, return_json: bool = False
    ) -> List[TestResult]:
        """
        Runs all tests using subprocess and records the results.

        Args:
            return_json (bool): Whether to return results in JSON format.

        Returns:
            List[TestResult]: A list of test results (success or failure).
        """
        test_files = os.listdir(self.dir_path)
        logger.info(f"Running tests from directory: {self.dir_path}")

        for test_file in test_files:
            if test_file.endswith(".py"):
                try:
                    # Run the test file using subprocess
                    result = subprocess.run(
                        [
                            "python",
                            os.path.join(self.dir_path, test_file),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    self.test_results.append(
                        TestResult(
                            class_name=test_file,
                            status="success",
                            message=result.stdout,
                        )
                    )
                    logger.info(f"Test {test_file} passed.")
                except subprocess.CalledProcessError as e:
                    self.test_results.append(
                        TestResult(
                            class_name=test_file,
                            status="failure",
                            message=e.stderr,
                        )
                    )
                    logger.error(
                        f"Test {test_file} failed with error: {e.stderr}"
                    )

        if return_json:
            return [result.json() for result in self.test_results]
        return self.test_results

    def check_tests_results(self, return_json: bool = False):
        """
        Main method to generate and run all tests.

        Args:
            return_json (bool): Whether to return results in JSON format.
        """
        logger.info("Starting test generation and execution.")
        self.generate_tests()
        results = self.run_all_tests(return_json=return_json)
        if return_json:
            logger.info("Returning results in JSON format.")
            print(results)
        else:
            for result in results:
                logger.info(
                    f"{result.class_name} - {result.status}: {result.message}"
                )
                print(
                    f"{result.class_name} - {result.status}: {result.message}"
                )

    def run(self, return_json: bool = False):
        """
        Main method to generate and run all tests.

        Args:
            return_json (bool): Whether to return results in JSON format.
        """
        logger.info("Starting test generation and execution.")
        self.generate_tests()

        return self.log.model_dump_json(indent=2)
