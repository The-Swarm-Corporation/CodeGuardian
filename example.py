from code_guardian.main import CodeGuardian
import os

from dotenv import load_dotenv
from swarms import Agent, OpenAIChat


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
    # system_prompt="Generate unit tests for the provided classes using pytest. Return the code in a code block and nothing else.",  # Updated system prompt
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


# from swarm_models.base_embedding_model import BaseEmbeddingModel
from swarm_models.base_llm import BaseLLM  # noqa: E402
from swarm_models.base_multimodal_model import BaseMultiModalModel
from swarm_models.fuyu import Fuyu  # noqa: E402
from swarm_models.gpt4_vision_api import GPT4VisionAPI  # noqa: E402
from swarm_models.huggingface import HuggingfaceLLM  # noqa: E402
from swarm_models.idefics import Idefics  # noqa: E402


#############################


# Classes you want to generate tests for
models_list = [
    BaseLLM,
    BaseMultiModalModel,
    Fuyu,
    GPT4VisionAPI,
    HuggingfaceLLM,
    Idefics,
]

# Initialize CodeGuardian and run
guardian = CodeGuardian(
    classes=models_list,  # classes to test
    # agent=agent,  # agent to use
    dir_path="tests",  # directory to save tests
    package_name="swarm_models",  # package name
    module_name="swarm_models",  # module name
    # agent=prebuilt_agent,
    # model=model,
    agent=agent,
)

guardian.run()
