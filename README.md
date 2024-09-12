
# Code Guardian

**Generate tests with swarms of agents**

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20our%20server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/agora-999382051935506503) [![Subscribe on YouTube](https://img.shields.io/badge/YouTube-Subscribe-red?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@kyegomez3242) [![Connect on LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/kye-g-38759a207/) [![Follow on X.com](https://img.shields.io/badge/X.com-Follow-1DA1F2?style=for-the-badge&logo=x&logoColor=white)](https://x.com/kyegomezb)


**CodeGuardian** is an intelligent agent designed to automate the generation of production-grade unit tests for your Python code. It not only creates and runs these tests but also monitors them in real-time, providing you with comprehensive summaries of your code health. With CodeGuardian, you can enhance code reliability, maintainability, and accelerate your development workflow.

## Features

- **Automated Test Generation**: Automatically generate unit tests for your existing Python codebase.
- **Test Execution**: Run generated tests seamlessly and view results instantly.
- **Real-Time Monitoring**: Watch tests in real-time to observe code behavior and performance.
- **Code Health Summaries**: Receive detailed reports on test coverage, code quality, and potential issues.
- **Easy Integration**: Integrate effortlessly with existing projects and CI/CD pipelines.
- **Customizable Configurations**: Tailor settings to match your project requirements.


### Prerequisites

- **Python 3.7** or higher
- **pip** package manager


## Installation
```bash
pip3 install -U code-guardian
```

## Example

```python
import os

from dotenv import load_dotenv
from swarms import Agent, OpenAIChat

from code_guardian.main import CodeGuardian

load_dotenv()

# Get the OpenAI API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Create an instance of the OpenAIChat class
model = OpenAIChat(
    openai_api_key=api_key,
    model_name="gpt-4o-mini",
    temperature=0.1,
    max_tokens=2000,
)

# Initialize the agent for generating unit tests
agent = Agent(
    agent_name="Unit-Test-Generator-Agent",  # Changed agent name
    system_prompt="Generate unit tests for the provided classes using pytest.",  # Updated system prompt
    llm=model,
    max_loops=1,
    autosave=True,
    dashboard=False,
    verbose=True,
    dynamic_temperature_enabled=True,
    saved_state_path="unit_test_agent.json",  # Updated saved state path
    user_name="swarms_corp",
    retry_attempts=1,
    context_length=200000,
    return_step_meta=False,
    # output_type="json",
)

# Classes you want to generate tests for
classes_to_test = [CodeGuardian]

# Initialize CodeGuardian and run
guardian = CodeGuardian(
    classes=classes_to_test, # classes to test
    agent=agent, # agent to use
    dir_path="tests", # directory to save tests
    package_name="code-guardian", # package name
    module_name="code_guardian.main", # module name
)
guardian.run()
```


### Configuration Options

- **test_directory**: Directory where tests are stored.
- **source_directory**: Directory containing your source code.
- **exclude_patterns**: Files or directories to exclude.
- **report_format**: Format of the code health report (`html`, `json`, `xml`).
- **watch**: Settings for real-time monitoring.


## Roadmap

- **Multi-language Support**: Extend functionality to other programming languages.
- **Advanced Static Analysis**: Integrate deeper code analysis tools.
- **IDE Plugins**: Develop plugins for popular IDEs like VSCode and PyCharm.
- **Enhanced Reporting**: Add more detailed metrics and visualizations.

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to get started.

## License

CodeGuardian is licensed under the [MIT License](LICENSE).

## Acknowledgements

- Inspired by the need for robust automated testing tools.
- Thanks to the open-source community for their invaluable contributions.
