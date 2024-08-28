import json
import os
import pickle
from opendatafit.datapackage import (
    load_resource_by_argument,
    load_resource,
    write_resource,
    load_argument_space,
    write_argument_space,
    RESOURCES_DIR,
    ALGORITHMS_DIR,
    VIEWS_DIR,
)
from importlib.machinery import SourceFileLoader


# Datapackage is mounted at /datapackage in container definition
DATAPACKAGE_PATH = os.getcwd() + "/datapackage"
resources_path = f"{DATAPACKAGE_PATH}/{RESOURCES_DIR}"
algorithms_path = f"{DATAPACKAGE_PATH}/{ALGORITHMS_DIR}"
views_path = f"{DATAPACKAGE_PATH}/{VIEWS_DIR}"


# Helpers


def execute():
    """Execute algorithm with specified container and argument resource"""

    algorithm_name = os.environ.get("ALGORITHM")

    # Load requested execution parameters from env vars
    if "CONTAINER" in os.environ:
        container_name = os.environ.get("CONTAINER")
    else:
        raise ValueError("CONTAINER environment variable missing")

    if "ARGUMENTS" in os.environ:
        argument_space_name = os.environ.get("ARGUMENTS")
    else:
        # TODO: Get this from the algorithm
        raise NotImplementedError(
            "Populating arguments from algorithm not yet implemented"
        )

    # Load algorithm
    # algorithm = load_json(algorithms_path + algorithm_name + ".json")
    # TODO Validate arguments against algorithm interface here

    # Load argument values
    argument_space = load_argument_space(
        algorithm_name, argument_space_name, base_path=DATAPACKAGE_PATH
    )

    # Populate dict of key: value argument pairs to pass to function
    kwargs = {}

    for argument in argument_space["data"]:
        argument_name = argument["name"]

        if "value" in argument:
            # Argument is a simple value
            kwargs[argument_name] = argument["value"]
        elif "resource" in argument:
            # Argument is a resource
            kwargs[argument_name] = load_resource_by_argument(
                algorithm_name,
                argument_name,
                argument_space_name,
                base_path=DATAPACKAGE_PATH,
            )

    # Import algorithm module
    # Import as "algorithm_module" here to avoid clashing with any library
    # names (e.g. bindfit.py algorithm vs. bindfit library)
    algorithm_module = SourceFileLoader(
        "algorithm_module", f"{algorithms_path}/{algorithm_name}.py"
    ).load_module()

    # Execute algorithm with kwargs
    result: dict = algorithm_module.main(**kwargs)

    # Populate argument resource with outputs and save
    for argument in argument_space["data"]:
        if argument["name"] in result.keys():
            # Update argument value/resource with algorithm output
            if "value" in argument:
                # Arg is a simple value
                argument["value"] = result[argument["name"]]
            elif "resource" in argument:
                # Arg is a resource, update the associated resource file
                # Get result resource
                updated_resource = result[argument["name"]].to_dict()

                # TODO: Validate updated_resource here - check it's a valid
                # resource of the type specified

                write_resource(updated_resource, base_path=DATAPACKAGE_PATH)

    # Update arguments resource metadata from environment variables
    argument_space["algorithm"] = algorithm_name
    argument_space["container"] = container_name

    # # TODO Validate argument outputs against algorithm interface

    # Save updated arguments resource
    write_argument_space(argument_space, base_path=DATAPACKAGE_PATH)


def view():
    """Render view in specified container"""
    view_name = os.environ.get("VIEW")

    # Load view
    with open(f"{views_path}/{view_name}.json", "r") as f:
        view = json.load(f)

    # Load associated resources
    resources = {}

    # TODO: Handle single resource case

    for resource_name in view["resources"]:
        # Load resource into TabularDataResource object
        resources[resource_name] = load_resource(
            resource_name, base_path=DATAPACKAGE_PATH
        )

    if view["specType"] == "matplotlib":
        # Import matplotlib module
        matplotlib_module = SourceFileLoader(
            "matplotlib_module", f"{views_path}/{view['specFile']}"
        ).load_module()

        # Pass resources and execute
        fig = matplotlib_module.main(**resources)

        # Save figure
        figpath = f"{views_path}/{view_name}"

        print(f"Saving image at {figpath}.png")
        fig.savefig(f"{figpath}.png")

        print(f"Saving object at {figpath}.p")
        with open(f"{figpath}.p", "wb") as f:
            pickle.dump(fig, f)


if __name__ == "__main__":
    if "ALGORITHM" in os.environ:
        execute()
    elif "VIEW" in os.environ:
        view()
    else:
        raise ValueError(
            "Must provide either ALGORITHM or VIEW environment variables"
        )
