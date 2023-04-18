import time

from openai.error import RateLimitError

from autogpt import token_counter
from autogpt.config import Config
from autogpt.llm_utils import create_chat_completion
from autogpt.logger import logger

cfg = Config()


def create_chat_message(role, content):
    """
    Create a chat message with the given role and content.

    Args:
    role (str): The role of the message sender, e.g., "system", "user", or "assistant".
    content (str): The content of the message.

    Returns:
    dict: A dictionary containing the role and content of the message.
    """
    return {"role": role, "content": content}


def generate_context(prompt, relevant_memory, full_message_history, model):
    current_context = [
        create_chat_message("system", prompt),
        create_chat_message(
            "system", f"The current time and date is {time.strftime('%c')}"
        ),
        create_chat_message(
            "system",
            f"This reminds you of these events from your past:\n{relevant_memory}\n\n",
        ),
    ]

    # Add messages from the full message history until we reach the token limit
    next_message_to_add_index = len(full_message_history) - 1
    insertion_index = len(current_context)
    # Count the currently used tokens
    current_tokens_used = token_counter.count_message_tokens(current_context, model)
    return (
        next_message_to_add_index,
        current_tokens_used,
        insertion_index,
        current_context,
    )


# TODO: Change debug from hardcode to argument
def chat_with_ai(
    prompt, user_input, full_message_history, permanent_memory, token_limit
):
    while True:
        try:
            model = cfg.fast_llm_model  # TODO: Change model from hardcode to argument
            (
                next_message_to_add_index,
                current_tokens_used,
                insertion_index,
                current_context,
            ) = generate_context(prompt, model)

            current_context.extend([create_chat_message("user", user_input)])

            assistant_reply = create_chat_completion(
                model=model,
                messages=current_context,
                max_tokens=tokens_remaining,
            )
            return assistant_reply
        except RateLimitError:
            print("Error: ", "API Rate Limit Reached. Waiting 10 seconds...")
            time.sleep(10)
