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
    system_prompt="Generate unit tests for the provided classes using pytest. Return the code in a code block and nothing else.",  # Updated system prompt
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
    classes=classes_to_test,
    agent=agent,
    dir_path="tests",
    package_name="code-guardian",
    module_name="code_guardian.main",
)
guardian.run()
