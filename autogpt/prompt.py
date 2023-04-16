from autogpt.promptgenerator import PromptGenerator


def get_prompt() -> str:
    """
    This function generates a prompt string that includes various constraints,
        commands, resources, and performance evaluations.

    Returns:
        str: The generated prompt string.
    """

    # Initialize the PromptGenerator object
    prompt_generator = PromptGenerator()

    # Add constraints to the PromptGenerator object
    prompt_generator.add_constraint(
        "Adhere to the provided list of commands and use them exclusively."
    )
    prompt_generator.add_constraint(
        "Ensure you use the correct arguments for each command."
    )
    prompt_generator.add_constraint(
        "Use your short-term memory wisely, as you are limited to ~4000 words.")
    prompt_generator.add_constraint(
        'Exclusively use the commands listed in double quotes e.g. "command name"'
    )
    prompt_generator.add_constraint(
        'Reflect on past decisions and strategies to refine your approach.'
    )
    prompt_generator.add_constraint(
        'Prioritize efficiency and smart decision-making.'
    )
    prompt_generator.add_constraint(
        'your strengths include efficient execution of tasks and effective delegation of simpler tasks to GPT powered agents. Use these strengths to navigate the constraints and work towards the goal'
    )

    # Define the command list
    commands = [
        ("Google Search", "google", {"input": "<search>"}),
        (
            "Browse Website",
            "browse_website",
            {"url": "<url>", "question": "<what_you_want_to_find_on_website>"},
        ),
        (
            "Start GPT Agent",
            "start_agent",
            {"name": "<name>", "task": "<short_task_desc>", "prompt": "<prompt>"},
        ),
        (
            "Message GPT Agent",
            "message_agent",
            {"key": "<key>", "message": "<message>"},
        ),
        ("List GPT Agents", "list_agents", {}),
        ("Delete GPT Agent", "delete_agent", {"key": "<key>"}),
        ("Write to file", "write_to_file", {"file": "<file>", "text": "<text>"}),
        ("Read file", "read_file", {"file": "<file>"}),
        ("Append to file", "append_to_file", {"file": "<file>", "text": "<text>"}),
        ("Delete file", "delete_file", {"file": "<file>"}),
        ("Search Files", "search_files", {"directory": "<directory>"}),
        ("Evaluate Code", "evaluate_code", {"code": "<full_code_string>"}),
        (
            "Get Improved Code",
            "improve_code",
            {"suggestions": "<list_of_suggestions>", "code": "<full_code_string>"},
        ),
        (
            "Write Tests",
            "write_tests",
            {"code": "<full_code_string>", "focus": "<list_of_focus_areas>"},
        ),
        ("Execute Python File", "execute_python_file", {"file": "<file>"}),
        (
            "Execute Shell Command, non-interactive commands only",
            "execute_shell",
            {"command_line": "<command_line>"},
        ),
        ("Task Complete (Shutdown)", "task_complete", {"reason": "<reason>"}),
        ("Generate Image", "generate_image", {"prompt": "<prompt>"}),
        ("Do Nothing", "do_nothing", {}),
    ]

    # Add commands to the PromptGenerator object
    for command_label, command_name, args in commands:
        prompt_generator.add_command(command_label, command_name, args)

    # Add resources to the PromptGenerator object
    prompt_generator.add_resource(
        "Internet access: Utilize search engines and browse websites to gather information and learn new concepts to help you accomplish tasks."
    )
    prompt_generator.add_resource(
        "Long Term memory management: Employ your long-term memory to recall essential information, past experiences, and relevant knowledge to make better decisions."
    )
    prompt_generator.add_resource(
        "GPT-3.5 powered Agents: Delegate simple tasks to GPT-3.5 powered agents to save time and focus on more complex tasks that require your expertise."
    )
    prompt_generator.add_resource(
        "File output: Save, read, and manage files to organize and store vital information, ensuring you can quickly access and process data as needed."
    )
    # Add performance evaluations to the PromptGenerator object
    prompt_generator.add_performance_evaluation(
        "Regularly review and analyze your actions, identifying areas where you can improve and refine your decision-making process to perform at your best."
    )
    prompt_generator.add_performance_evaluation(
        "Engage in constructive self-criticism, focusing on your overall behavior and decision-making patterns to foster growth and development."
    )
    prompt_generator.add_performance_evaluation(
        "Reflect on previous decisions and strategies, learning from both successes and failures to continuously refine your approach and adapt to new challenges."
    )
    prompt_generator.add_performance_evaluation(
        "Be mindful of the cost of each command, striving for efficiency by completing tasks in the fewest steps possible without compromising on quality."
    )
    prompt_generator.add_performance_evaluation(
        "By following this optimized prompt, you will be better equipped to evaluate your performance, making necessary adjustments to maintain a high level of effectiveness in achieving your goals."
    )
    # Generate the prompt string
    return prompt_generator.generate_prompt_string()
