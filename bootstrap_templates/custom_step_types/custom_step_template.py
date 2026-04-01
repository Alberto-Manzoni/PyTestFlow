from pytestflow.steps.action_step import action_step


@action_step(name="my_custom_step")
def my_custom_step():
    return "Implement your custom logic here"

