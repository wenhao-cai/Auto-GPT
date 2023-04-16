import json


class PromptGenerator:
    """
    A class for generating custom prompt strings based on constraints, commands,
        resources, and performance evaluations.
    """

    def __init__(self):
        """
        Initialize the PromptGenerator object with empty lists of constraints,
            commands, resources, and performance evaluations.
        """
        self.constraints = []
        self.commands = []
        self.resources = []
        self.performance_evaluation = []
        self.response_format = {
            "thoughts": {
                "text": "thought",
                "reasoning": "reasoning",
                "plan": "- short bulleted\n- list that conveys\n- long-term plan",
                "criticism": "constructive self-criticism",
                "speak": "thoughts summary to say to user",
            },
            "command": {"name": "command name", "args": {"arg name": "value"}},
        }

    def add_constraint(self, constraint):
        """
        Add a constraint to the constraints list.

        Args:
            constraint (str): The constraint to be added.
        """
        self.constraints.append(constraint)

    def add_command(self, command_label, command_name, args=None):
        """
        Add a command to the commands list with a label, name, and optional arguments.

        Args:
            command_label (str): The label of the command.
            command_name (str): The name of the command.
            args (dict, optional): A dictionary containing argument names and their
              values. Defaults to None.
        """
        if args is None:
            args = {}

        command_args = {arg_key: arg_value for arg_key, arg_value in args.items()}

        command = {
            "label": command_label,
            "name": command_name,
            "args": command_args,
        }

        self.commands.append(command)

    def _generate_command_string(self, command):
        """
        Generate a formatted string representation of a command.

        Args:
            command (dict): A dictionary containing command information.

        Returns:
            str: The formatted command string.
        """
        args_string = ", ".join(
            f'"{key}": "{value}"' for key, value in command["args"].items()
        )
        return f'{command["label"]}: "{command["name"]}", args: {args_string}'

    def add_resource(self, resource: str) -> None:
        """
        Add a resource to the resources list.

        Args:
            resource (str): The resource to be added.
        """
        self.resources.append(resource)

    def add_performance_evaluation(self, evaluation: str) -> None:
        """
        Add a performance evaluation item to the performance_evaluation list.

        Args:
            evaluation (str): The evaluation item to be added.
        """
        self.performance_evaluation.append(evaluation)

    def _generate_numbered_list(self, items, item_type="list") -> str:
        """
        Generate a numbered list from given items based on the item_type.

        Args:
            items (list): A list of items to be numbered.
            item_type (str, optional): The type of items in the list.
                Defaults to 'list'.

        Returns:
            str: The formatted numbered list.
        """
        if item_type == "command":
            return "\n".join(
                f"{i+1}. {self._generate_command_string(item)}"
                for i, item in enumerate(items)
            )
        else:
            return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))

    def generate_prompt_string(self) -> str:
        """
        Generate a prompt string based on the constraints, commands, resources,
            and performance evaluations.

        Returns:
            str: The generated prompt string.
        """
        formatted_response_format = json.dumps(self.response_format, indent=4)
        return (
            f"When executing tasks, focus on the following:\n{self._generate_numbered_list(self.constraints)}\n\n"
            "Commands:\n"
            f"{self._generate_numbered_list(self.commands, item_type='command')}\n\n"
            f"Resources:\n{self._generate_numbered_list(self.resources)}\n"
            f"Remember to use these resources wisely and effectively in order to achieve your goals, combining your knowledge and skills to execute tasks efficiently and accurately. Always prioritize tasks based on their importance and urgency, and continuously review your actions to ensure optimal performance.\n\n"
            "Performance Evaluation:\n"
            f"{self._generate_numbered_list(self.performance_evaluation)}\n\n"
            "IMPORTANT: You must respond in JSON format as described below. Ensure that your response strictly adheres to JSON format rules and can be parsed by Python's json.loads function \nResponse"
            f" Format: \n{formatted_response_format}\n\n"
            f"Remember to answer in Chinese only."
        )
