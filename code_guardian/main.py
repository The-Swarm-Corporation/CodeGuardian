import concurrent.futures
import inspect
import os
import re
import subprocess
import time
from typing import Any, List

from loguru import logger
from pydantic import BaseModel, Field
from swarms import Agent

from code_guardian.prompt import TEST_WRITER_SOP_PROMPT


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
    dir_path: str
    package_name: str
    module_name: str


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
        agent: Agent = None,
        dir_path: str = "tests/memory",
        package_name: str = "swarms",
        module_name: str = "swarms.memory",
    ):
        self.classes = classes
        self.agent = agent
        self.dir_path = dir_path
        self.package_name = package_name
        self.module_name = module_name

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
            dir_path = dir_path,
            package_name = package_name,
            module_name = module_name,
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
        """Generates test files and runs them until successful."""
        class_name = cls.__name__

        # Retrieve class documentation and source code
        doc, source = self.get_class_details(cls)
        input_content = self.prepare_input_content(
            class_name, doc, source
        )
        prompt = TEST_WRITER_SOP_PROMPT(
            input_content, self.package_name, self.module_name
        )

        # Initialize result list for context tracking
        results = [prompt]

        try:
            while True:  # Keep running until the test passes
                logger.debug(
                    f"Generating test code for class {class_name}"
                )

                # Generate test code using agent
                test_code = self.generate_test_code(prompt)
                results.append(test_code)

                # Create and write the test file
                file_path = self.write_test_file(
                    class_name, test_code
                )

                # Run the test
                test_output = self.run_test_file(test_code)
                results.append(test_output)

                if (
                    "failed" not in test_output
                ):  # Break the loop if the test is successful
                    logger.info(
                        f"Test for {class_name} passed successfully."
                    )
                    self.log_test(
                        class_name=class_name,
                        doc=doc,
                        source=source,
                        test_code=test_code,
                        file_path=file_path,
                        error_message=test_output,
                        status="failure",
                    )
                    break
                else:
                    logger.warning(
                        f"Test for {class_name} failed. Retrying with updated context."
                    )
                    self.log_test(
                        class_name=class_name,
                        doc=doc,
                        source=source,
                        test_code=test_code,
                        file_path=file_path,
                        error_message=test_output,
                        status="success",
                    )
                    prompt = self.concat_results_for_retry(results)

        except Exception as e:
            logger.error(
                f"Error while creating test for class {class_name}: {e}"
            )
            self.log_test_failure(
                class_name, "N/A", f"Exception: {str(e)}"
            )

    # def generate_tests(self):
    #     """Generates test files for all classes concurrently."""
    #     logger.info("Starting test generation for all classes.")

    #     # Use ThreadPoolExecutor for concurrent execution
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         futures = {executor.submit(self.create_test, cls): cls for cls in self.classes}
    #         for future in concurrent.futures.as_completed(futures):
    #             cls = futures[future]
    #             try:
    #                 future.result()
    #             except Exception as e:
    #                 logger.error(f"Error generating test for class {cls}: {e}")

    #     logger.info("Test generation finished.")
    
    # def generate_tests(self):
    #     """Generates test files for all classes concurrently."""
    #     logger.info("Starting test generation for all classes.")

    #     # Use ThreadPoolExecutor for concurrent execution
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         futures = {executor.submit(self.create_test, cls): cls for cls in self.classes}
    #         for future in concurrent.futures.as_completed(futures):
    #             cls = futures[future]
    #             try:
    #                 future.result()  # Each class handled in isolated threads
    #             except Exception as e:
    #                 logger.error(f"Error generating test for class {cls}: {e}")

    #     logger.info("Test generation finished.")
    
    def generate_tests(self):
        for cls in self.classes:
            self.create_test(cls)
            
        logger.info(f"Finished creating tests")


    def run_test_file(self, file_name: str) -> str:
        """
        Runs a specified test file using subprocess.

        Args:
            file_name (str): The name of the test file to run.

        Returns:
            str: The output or error message from the test execution.
        """
        file_path = os.path.abspath(
            os.path.join(self.dir_path, file_name)
        )  # Ensure full path

        # Ensure the file exists before attempting to execute it
        if not os.path.exists(file_path):
            logger.error(f"Test file {file_path} does not exist.")
            return f"Error: Test file {file_path} does not exist."

        try:
            # Run the test file using an absolute path with subprocess
            logger.debug(
                f"Attempting to run test file at: {file_path}"
            )

            result = subprocess.run(
                ["python3", file_path],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info(
                f"Test {file_name} ran successfully with output:\n{result.stdout}"
            )
            return f"Test {file_name} ran successfully with output:\n{result.stdout}"

        except subprocess.CalledProcessError as e:
            logger.error(
                f"Test {file_name} failed with error:\n{e.stderr}"
            )
            return f"Test {file_name} failed with error:\n{e.stderr}"

    def run(self, return_json: bool = False):
        """
        Main method to generate and run all tests.

        Args:
            return_json (bool): Whether to return results in JSON format.
        """
        self.generate_tests()
        logger.info("Test generation finished.")

        return self.log.model_dump_json(indent=2)

    def get_class_details(self, cls: Any):
        """Retrieves the class docstring and source code."""
        doc = inspect.getdoc(cls)
        source = inspect.getsource(cls)
        return doc, source

    def prepare_input_content(
        self, class_name: str, doc: str, source: str
    ) -> str:
        """Prepares the input content for the agent based on class details."""
        return f"Class Name: {class_name}\n\nDocumentation:\n{doc}\n\nSource Code:\n{source}"

    def generate_test_code(self, prompt: str) -> str:
        """Generates the test code by running the agent with the provided prompt."""
        processed_content = self.agent.run(prompt)
        return self.extract_code_from_markdown(processed_content)

    def write_test_file(self, class_name: str, test_code: str) -> str:
        """
        Writes the generated test code to a file.

        Args:
            class_name (str): The name of the class being tested.
            test_code (str): The test code to be written to the file.

        Returns:
            str: The full path of the written test file.
        """
        os.makedirs(self.dir_path, exist_ok=True)

        # Convert class name to a safe file name
        safe_class_name = self.sanitize_class_name(class_name)

        # Construct the file path
        file_path_name = f"test_{safe_class_name}.py"
        file_path = os.path.join(self.dir_path, file_path_name)

        # Write the test code to the file
        with open(file_path, "w") as file:
            file.write(f"# {class_name}\n\n{test_code}\n")

        # Log the class name and file path for debugging
        logger.debug(f"Class name: {class_name}")
        logger.debug(f"Safe file name: {file_path_name}")
        logger.debug(f"Test file written to: {file_path}")

        return file_path

    def sanitize_class_name(self, class_name: str) -> str:
        """
        Sanitizes the class name to be used as a file name.

        Args:
            class_name (str): The original class name.

        Returns:
            str: A sanitized version of the class name safe for file names.
        """
        # Replace any non-alphanumeric characters with underscores and convert to lowercase
        return re.sub(r"[^a-zA-Z0-9]", "_", class_name).lower()

    def concat_results_for_retry(self, results: list) -> str:
        """Concatenates all result strings into a single prompt for retry attempts."""
        return "\n".join(results)

    def log_test(
        self,
        class_name: str,
        doc: str,
        source: str,
        test_code: str,
        file_path: str,
        error_message: str,
        status: str,
    ):
        """Logs the test failure."""
        self.log.tests.append(
            TestResult(
                class_name=class_name,
                class_docstring=doc,
                class_source_code=source,
                test_file_path=file_path,
                test_file_content=test_code,
                status=status,
                message=error_message,
            )
        )
        logger.warning(
            f"Test {status} logged for {class_name} with message:\n{error_message}"
        )
