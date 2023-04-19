import argparse
import json
import logging
import traceback

from colorama import Fore, Style

from autogpt import chat
from autogpt import commands as cmd
from autogpt import speak, utils
from autogpt.ai_config import AIConfig
from autogpt.config import Config
from autogpt.json_parser import fix_and_parse_json
from autogpt.logger import logger
from autogpt.memory import get_memory, get_supported_memory_backends
from autogpt.spinner import Spinner
from autogpt.CustomOpenAI import CustomOpenAI
from autogpt.promptgenerator import PromptGenerator

cfg = Config()
config = None


def check_openai_api_key():
    """Check if the OpenAI API key is set in config.py or as an environment variable."""
    if not cfg.openai_api_key:
        print(
            Fore.RED
            + "Please set your OpenAI API key in .env or as an environment variable."
        )
        print("You can get your key from https://beta.openai.com/account/api-keys")
        exit(1)


def attempt_to_fix_json_by_finding_outermost_brackets(json_string):
    if cfg.speak_mode and cfg.debug_mode:
        speak.say_text(
            "I have received an invalid JSON response from the OpenAI API. "
            "Trying to fix it now."
        )
    logger.typewriter_log("Attempting to fix JSON by finding outermost brackets\n")

    try:
        # Use regex to search for JSON objects
        import regex

        json_pattern = regex.compile(r"\{(?:[^{}]|(?R))*\}")
        json_match = json_pattern.search(json_string)

        if json_match:
            # Extract the valid JSON object from the string
            json_string = json_match.group(0)
            logger.typewriter_log(
                title="Apparently json was fixed.", title_color=Fore.GREEN
            )
            if cfg.speak_mode and cfg.debug_mode:
                speak.say_text("Apparently json was fixed.")
        else:
            raise ValueError("No valid JSON object found")

    except (json.JSONDecodeError, ValueError) as e:
        if cfg.debug_mode:
            logger.error("Error: Invalid JSON: %s\n", json_string)
        if cfg.speak_mode:
            speak.say_text("Didn't work. I will have to ignore this response then.")
        logger.error("Error: Invalid JSON, setting it to empty JSON now.\n")
        json_string = {}

    return json_string


def print_assistant_thoughts(assistant_reply):
    """Prints the assistant's thoughts to the console"""
    global ai_name
    global cfg
    try:
        try:
            # Parse and print Assistant response
            assistant_reply_json = fix_and_parse_json(assistant_reply)
        except json.JSONDecodeError as e:
            logger.error("Error: Invalid JSON in assistant thoughts\n", assistant_reply)
            assistant_reply_json = attempt_to_fix_json_by_finding_outermost_brackets(
                assistant_reply
            )
            assistant_reply_json = fix_and_parse_json(assistant_reply_json)

        # Check if assistant_reply_json is a string and attempt to parse it into a
        #  JSON object
        if isinstance(assistant_reply_json, str):
            try:
                assistant_reply_json = json.loads(assistant_reply_json)
            except json.JSONDecodeError as e:
                logger.error("Error: Invalid JSON\n", assistant_reply)
                assistant_reply_json = (
                    attempt_to_fix_json_by_finding_outermost_brackets(
                        assistant_reply_json
                    )
                )

        assistant_thoughts_reasoning = None
        assistant_thoughts_plan = None
        assistant_thoughts_speak = None
        assistant_thoughts_criticism = None
        assistant_thoughts = assistant_reply_json.get("thoughts", {})
        assistant_thoughts_text = assistant_thoughts.get("text")

        if assistant_thoughts:
            assistant_thoughts_reasoning = assistant_thoughts.get("reasoning")
            assistant_thoughts_plan = assistant_thoughts.get("plan")
            assistant_thoughts_criticism = assistant_thoughts.get("criticism")
            assistant_thoughts_speak = assistant_thoughts.get("speak")

        if assistant_thoughts_plan:
            logger.typewriter_log("PLAN:", Fore.YELLOW, "")
            # If it's a list, join it into a string
            if isinstance(assistant_thoughts_plan, list):
                assistant_thoughts_plan = "\n".join(assistant_thoughts_plan)
            elif isinstance(assistant_thoughts_plan, dict):
                assistant_thoughts_plan = str(assistant_thoughts_plan)

            # Split the input_string using the newline character and dashes
            lines = assistant_thoughts_plan.split("\n")
            for line in lines:
                line = line.lstrip("- ")
                logger.typewriter_log("- ", Fore.GREEN, line.strip())

        # Speak the assistant's thoughts
        if cfg.speak_mode and assistant_thoughts_speak:
            speak.say_text(assistant_thoughts_speak)

        return assistant_reply_json
    except json.decoder.JSONDecodeError:
        call_stack = traceback.format_exc()
        logger.error("Error: Invalid JSON\n", assistant_reply)
        logger.error("Traceback: \n", call_stack)
        if cfg.speak_mode:
            speak.say_text(
                "I have received an invalid JSON response from the OpenAI API."
                " I cannot ignore this response."
            )

    # All other errors, return "Error: + error message"
    except Exception:
        call_stack = traceback.format_exc()
        logger.error("Error: \n", call_stack)


def construct_prompt():
    """Construct the prompt for the AI to respond to"""
    config: AIConfig = AIConfig.load(cfg.ai_settings_file)
    if config.ai_name:
        should_continue = utils.clean_input(
            f"""Continue with the last settings?
Name:  {config.ai_name}
Role:  {config.ai_role}
Goals: {config.ai_goals}
ID: {config.ai_conversation_id}
Continue (y/n): """
        )
        if should_continue.lower() == "n":
            config = AIConfig()

    if not config.ai_name:
        config = prompt_user()
        config.save()

    # Get rid of this global:
    global ai_name
    ai_name = config.ai_name

    return config.construct_full_prompt()


def prompt_user():
    """Prompt the user for input"""
    ai_name = ""

    ai_name = utils.clean_input("AI Name: ")
    if ai_name == "":
        ai_name = "Entrepreneur-GPT"

    ai_role = utils.clean_input(f"{ai_name} is: ")
    if ai_role == "":
        ai_role = "an AI designed to autonomously develop and run businesses with the"
        " sole goal of increasing your net worth."
    else:
        ai_role = f"{ai_role}\n Please provide explanations in Chinese while addressing the following:"

    print("Enter nothing to load defaults, enter nothing when finished.", flush=True)
    ai_goals = []
    for i in range(5):
        ai_goal = utils.clean_input(f"{Fore.LIGHTBLUE_EX}Goal{Style.RESET_ALL} {i+1}: ")
        if ai_goal == "":
            break
        ai_goals.append(ai_goal)
    if len(ai_goals) == 0:
        ai_goals = [
            "Increase net worth",
            "Grow Twitter Account",
            "Develop and manage multiple businesses autonomously",
        ]

    config = AIConfig(ai_name, ai_role, ai_goals)
    return config


def parse_arguments():
    """Parses the arguments passed to the script"""
    global cfg
    cfg.set_debug_mode(False)
    cfg.set_continuous_mode(False)
    cfg.set_speak_mode(False)

    parser = argparse.ArgumentParser(description="Process arguments.")
    parser.add_argument(
        "--continuous", "-c", action="store_true", help="Enable Continuous Mode"
    )
    parser.add_argument(
        "--continuous-limit",
        "-l",
        type=int,
        dest="continuous_limit",
        help="Defines the number of times to run in continuous mode",
    )
    parser.add_argument("--speak", action="store_true", help="Enable Speak Mode")
    parser.add_argument("--debug", action="store_true", help="Enable Debug Mode")
    parser.add_argument(
        "--gpt3only", action="store_true", help="Enable GPT3.5 Only Mode"
    )
    parser.add_argument("--gpt4only", action="store_true", help="Enable GPT4 Only Mode")
    parser.add_argument(
        "--use-memory",
        "-m",
        dest="memory_type",
        help="Defines which Memory backend to use",
    )
    parser.add_argument(
        "--skip-reprompt",
        "-y",
        dest="skip_reprompt",
        action="store_true",
        help="Skips the re-prompting messages at the beginning of the script",
    )
    parser.add_argument(
        "--ai-settings",
        "-C",
        dest="ai_settings_file",
        help="Specifies which ai_settings.yaml file to use, will also automatically"
        " skip the re-prompt.",
    )
    args = parser.parse_args()

    if args.debug:
        logger.typewriter_log("Debug Mode: ", Fore.GREEN, "ENABLED")
        cfg.set_debug_mode(True)

    if args.continuous:
        logger.typewriter_log("Continuous Mode: ", Fore.RED, "ENABLED")
        logger.typewriter_log(
            "WARNING: ",
            Fore.RED,
            "Continuous mode is not recommended. It is potentially dangerous and may"
            " cause your AI to run forever or carry out actions you would not usually"
            " authorise. Use at your own risk.",
        )
        cfg.set_continuous_mode(True)

        if args.continuous_limit:
            logger.typewriter_log(
                "Continuous Limit: ", Fore.GREEN, f"{args.continuous_limit}"
            )
            cfg.set_continuous_limit(args.continuous_limit)

    # Check if continuous limit is used without continuous mode
    if args.continuous_limit and not args.continuous:
        parser.error("--continuous-limit can only be used with --continuous")

    if args.speak:
        logger.typewriter_log("Speak Mode: ", Fore.GREEN, "ENABLED")
        cfg.set_speak_mode(True)

    if args.gpt3only:
        logger.typewriter_log("GPT3.5 Only Mode: ", Fore.GREEN, "ENABLED")
        cfg.set_smart_llm_model(cfg.fast_llm_model)

    if args.gpt4only:
        logger.typewriter_log("GPT4 Only Mode: ", Fore.GREEN, "ENABLED")
        cfg.set_fast_llm_model(cfg.smart_llm_model)

    if args.memory_type:
        supported_memory = get_supported_memory_backends()
        chosen = args.memory_type
        if not chosen in supported_memory:
            logger.typewriter_log(
                "ONLY THE FOLLOWING MEMORY BACKENDS ARE SUPPORTED: ",
                Fore.RED,
                f"{supported_memory}",
            )
            logger.typewriter_log("Defaulting to: ", Fore.YELLOW, cfg.memory_backend)
        else:
            cfg.memory_backend = chosen

    if args.skip_reprompt:
        logger.typewriter_log("Skip Re-prompt: ", Fore.GREEN, "ENABLED")
        cfg.skip_reprompt = True

    if args.ai_settings_file:
        file = args.ai_settings_file

        # Validate file
        (validated, message) = utils.validate_yaml_file(file)
        if not validated:
            logger.typewriter_log("FAILED FILE VALIDATION", Fore.RED, message)
            logger.double_check()
            exit(1)

        logger.typewriter_log("Using AI Settings File:", Fore.GREEN, file)
        cfg.ai_settings_file = file
        cfg.skip_reprompt = True


def main():
    global ai_name
    check_openai_api_key()
    parse_arguments()
    ai_name = ""
    ai_conversation_id = ""
    
    prompt = construct_prompt()
    next_action_count = 0
    # Make a constant:
    user_input = (
        "Determine which next command to use, and respond using the"
        " format specified above:"
    )

    agent = Agent(
        ai_name=ai_name,
        conversation_id=ai_conversation_id,
        next_action_count=next_action_count,
        prompt=prompt,
        user_input=user_input,
    )
    agent.start_interaction_loop()


class Agent:
    def __init__(
        self,
        ai_name,
        conversation_id,
        next_action_count,
        prompt,
        user_input,
    ):
        self.ai_name = ai_name
        self.next_action_count = next_action_count
        self.prompt = prompt
        self.user_input = user_input
        self.custom_api = CustomOpenAI(
            api_base_url="http://10.40.4.133:8008", token_name="caiwenhao2023")
        self.model = "text-davinci-002-render-sha"
        # self.conversation_id = "31ea23ca-e173-451c-806a-cc10ea95fa21"
        self.conversation_id = conversation_id
        if self.conversation_id:
            conversation = self.custom_api.get_conversation(self.conversation_id)
            self.last_message_id = conversation["current_node"]
        else:
            self.last_message_id = ""

        prompt_generator = PromptGenerator()
        self.prompt2 = prompt_generator.generate_prompt_string2()

    def start_interaction_loop(self):
        # Interaction Loop
        loop_count = 0
        command_name = None
        arguments = None
        while True:
            loop_count += 1
            if (
                cfg.continuous_mode
                and cfg.continuous_limit > 0
                and loop_count > cfg.continuous_limit
            ):
                break

            # Send message to AI, get response
            with Spinner("Thinking... "):
                if cfg.debug_mode:
                    print(f"向openai 发起prompt:\n{self.prompt}\n{self.user_input}")
                response = self.custom_api.talk(prompt=f"{self.prompt}\n\n User: {self.user_input}", model=self.model,
                                                parent_message_id=self.last_message_id, conversation_id=self.conversation_id)
                assistant_reply = response["message"]["content"]["parts"][0]
                self.conversation_id = response["conversation_id"]
                self.last_message_id = response["message"]["id"]
                config: AIConfig = AIConfig.load(cfg.ai_settings_file)
                config.ai_conversation_id = self.conversation_id
                config.save()
                

            # Print Assistant thoughts
            if cfg.debug_mode:
                print(f"openai 响应:\n{response}")
            print_assistant_thoughts(assistant_reply)

            # Get command name and arguments
            try:
                command_name, arguments = cmd.get_command(
                    attempt_to_fix_json_by_finding_outermost_brackets(assistant_reply)
                )
                print(f"提取到的命令{command_name}, 提取到的参数 {arguments}")
                if cfg.speak_mode:
                    speak.say_text(f"I want to execute {command_name}")
            except Exception as e:
                logger.error("Error: \n", str(e))

            if not cfg.continuous_mode and self.next_action_count == 0:
                ### GET USER AUTHORIZATION TO EXECUTE COMMAND ###
                # Get key press: Prompt the user to press enter to continue or escape
                # to exit
                self.user_input = ""
                print(
                    "Enter 'y' to authorise command, 'y -N' to run N continuous"
                    " commands, 'n' to exit program, or enter feedback for"
                    f" {self.ai_name}...",
                    flush=True,
                )
                while True:
                    console_input = utils.clean_input(
                        Fore.MAGENTA + "Input:" + Style.RESET_ALL
                    )
                    if console_input.lower().rstrip() == "y":
                        self.user_input = "根据上面的命令执行结果, 给出下一步json响应"
                        break
                    elif console_input.lower().startswith("y -"):
                        try:
                            self.next_action_count = abs(
                                int(console_input.split(" ")[1])
                            )
                            self.user_input = "根据上面的命令执行结果, 给出下一步json响应"
                        except ValueError:
                            print(
                                "Invalid input format. Please enter 'y -n' where n"
                                " is the number of continuous tasks."
                            )
                            continue
                        break
                    elif console_input.lower() == "n":
                        self.user_input = "EXIT"
                        break
                    else:
                        self.user_input = console_input
                        command_name = "human_feedback"
                        break

                if self.user_input == "根据上面的命令执行结果, 给出下一步json响应":
                    logger.typewriter_log(
                        "-=-=-=-=-=-=-= COMMAND AUTHORISED BY USER -=-=-=-=-=-=-=",
                        Fore.MAGENTA,
                        "",
                    )
                elif self.user_input == "EXIT":
                    print("Exiting...", flush=True)
                    break
            else:
                # Print command
                logger.typewriter_log(
                    "NEXT ACTION: ",
                    Fore.CYAN,
                    f"COMMAND = {Fore.CYAN}{command_name}{Style.RESET_ALL}"
                    f"  ARGUMENTS = {Fore.CYAN}{arguments}{Style.RESET_ALL}",
                )

            # Execute command
            if command_name is not None and command_name.lower().startswith("error"):
                result = (
                    f"Command {command_name} threw the following error: {arguments}"
                )
            elif command_name == "human_feedback":
                result = f"Human feedback: {self.user_input}"
            else:
                result = (
                    f"Command {command_name} "
                    f"returned: {cmd.execute_command(command_name, arguments)}"
                )
                if self.next_action_count > 0:
                    self.next_action_count -= 1

            if result is not None:
                self.prompt = f"{str(result)}"
            else:
                self.prompt = f"Unable to execute command"


if __name__ == "__main__":
    main()
