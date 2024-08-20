import json
import os
import pickle
from opendatafit.resources import TabularDataResource
from opendatafit.datapackage import load_resource_by_argument, write_resource
from importlib.machinery import SourceFileLoader


# Datapackage is mounted at /datapackage in container definition
DATAPACKAGE_PATH = os.getcwd() + "/datapackage"
RESOURCES_PATH = DATAPACKAGE_PATH + "/resources"
METASCHEMAS_PATH = DATAPACKAGE_PATH + "/metaschemas"
ALGORITHMS_PATH = DATAPACKAGE_PATH + "/algorithms"
ARGUMENTS_PATH = DATAPACKAGE_PATH + "/arguments"
VIEWS_PATH = DATAPACKAGE_PATH + "/views"


# Helpers


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, value):
    with open(path, "w") as f:
        json.dump(value, f, indent=2)


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
    # algorithm = load_json(ALGORITHMS_PATH + algorithm_name + ".json")
    # TODO Validate arguments against algorithm interface here

    # Load argument values
    argument_space = load_json(
        f"{ARGUMENTS_PATH}/{algorithm_name}.{argument_space_name}.json"
    )

    # Populate dict of key: value argument pairs to pass to function
    kwargs = {}

    # TODO: Merge this whole thing into the load_resource_by_argument function

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
        "algorithm_module", f"{ALGORITHMS_PATH}/{algorithm_name}.py"
    ).load_module()

    # Execute algorithm with kwargs
    result: dict = algorithm_module.main(**kwargs)

    # Populate argument resource with outputs and save
    for arg in argument_space["data"]:
        if arg["name"] in result.keys():
            # TODO: Write write_argument function to help with this

            # Update argument value/resource with algorithm output
            if "value" in arg:
                # Arg is a simple value
                arg["value"] = result[arg["name"]]
            elif "resource" in arg:
                # Arg is a resource, update the associated resource file
                # Get result resource
                updated_resource = result[arg["name"]].to_dict()

                # TODO: Validate updated_resource here - check it's a valid
                # resource of the type specified

                write_resource(updated_resource, base_path=DATAPACKAGE_PATH)

    # Update arguments resource metadata from environment variables
    argument_space["algorithm"] = algorithm_name
    argument_space["container"] = container_name

    # # TODO Validate argument outputs against algorithm interface

    # Save updated arguments resource
    save_json(
        path=f"{ARGUMENTS_PATH}/{algorithm_name}.{argument_space_name}.json",
        value=argument_space,
    )


def view():
    """Render view in specified container"""
    view_name = os.environ.get("VIEW")

    # Load view
    with open(f"{VIEWS_PATH}/{view_name}.json", "r") as f:
        view = json.load(f)

    # Load associated resources

    # TODO: Think about rewriting TabularDataResource to do handling of
    # metaschemas and validation that entrypoint does so we don't have to
    # redo it here

    # TODO: Handle single resource case

    resources = {}

    for resource_name in view["resources"]:
        # Load resource into TabularDataResource object
        with open(f"{RESOURCES_PATH}/{resource_name}.json", "r") as f:
            resource = json.load(f)
            # TODO: Temporary, populate "metaschema" key to avoid emtpy
            # metaschema error - we don't need it for this
            # This will go away when we handle metaschemas and validation
            # inside the object
            resource["metaschema"] = {"hello": "world"}
            resources[resource_name] = TabularDataResource(resource=resource)

    if view["specType"] == "matplotlib":
        # Import matplotlib module
        matplotlib_module = SourceFileLoader(
            "matplotlib_module", f"{VIEWS_PATH}/{view['specFile']}"
        ).load_module()

        # Pass resources and execute
        fig = matplotlib_module.main(**resources)

        # Save figure
        figpath = f"{VIEWS_PATH}/{view_name}"

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
