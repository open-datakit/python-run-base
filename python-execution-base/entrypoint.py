import json
import os
import pickle
from copy import deepcopy
from opendatafit.resources import TabularDataResource
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
        arguments_name = os.environ.get("ARGUMENTS")
    else:
        # TODO: Get this from the algorithm
        raise NotImplementedError(
            "Populating arguments from algorithm not yet implemented"
        )

    # Load algorithm
    # algorithm = load_json(ALGORITHMS_PATH + algorithm_name + ".json")
    # TODO Validate arguments against algorithm interface here

    # Load argument values
    arguments_resource = load_json(
        f"{ARGUMENTS_PATH}/{algorithm_name}.{arguments_name}.json"
    )

    # Populate dict of key: value argument pairs to pass to function
    kwargs = {}

    for arg in arguments_resource["data"]:
        name = arg["name"]
        if "value" in arg:
            kwargs[name] = arg["value"]
        elif "resource" in arg:
            resource_name = arg["resource"]
            resource_path = f"{RESOURCES_PATH}/{resource_name}.json"

            # Load resource JSON
            resource = load_json(resource_path)

            # Check resource is populated
            if resource is None:
                raise ValueError("Tried to load an empty resource")

            if (
                resource["profile"] == "tabular-data-resource"
                or resource["profile"] == "parameter-tabular-data-resource"
            ):
                # Load tabular data resource metaschema
                # TODO: Should this be done in TabularDataResource?
                try:
                    metaschema_path = (
                        f"{METASCHEMAS_PATH}/{arg['metaschema']}.json"
                    )
                    resource["metaschema"] = load_json(metaschema_path)[
                        "schema"
                    ]
                except KeyError:
                    raise KeyError(
                        (
                            "Argument for tabular data resource {}"
                            "does not specify metaschema"
                        ).format(resource["name"]),
                    )

                # Populate schema from metaschema if specified
                # TODO: Should this be done in TabularDataResource?
                if resource["schema"] == "metaschema":
                    schema = deepcopy(resource["metaschema"])

                    # Remove index from fields
                    fields = []
                    for field in schema["fields"]:
                        del field["index"]
                        fields.append(field)

                    schema["fields"] = fields

                    resource["schema"] = schema

            # Load resource into algorithm kwargs in required format
            if (
                resource["profile"] == "tabular-data-resource"
                or resource["profile"] == "parameter-tabular-data-resource"
            ):
                kwargs[name] = TabularDataResource(resource=resource)
            else:
                kwargs[name] = resource

    # Import algorithm module
    # Import as "algorithm_module" here to avoid clashing with any library
    # names (e.g. bindfit.py algorithm vs. bindfit library)
    algorithm_module = SourceFileLoader(
        "algorithm_module", f"{ALGORITHMS_PATH}/{algorithm_name}.py"
    ).load_module()

    # Execute algorithm with kwargs
    result: dict = algorithm_module.main(**kwargs)

    # Populate argument resource with outputs and save
    for arg in arguments_resource["data"]:
        if arg["name"] in result.keys():
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

                # Remove metaschema
                # TODO: Should we be adding/removing metaschemas inside
                # TabularDataResource object?
                updated_resource.pop("metaschema")

                # Load original resource JSON to check schema location
                resource_name = arg["resource"]
                resource_path = f"{RESOURCES_PATH}/{resource_name}.json"
                resource = load_json(resource_path)

                if resource["schema"] == "metaschema":
                    # External schema - preserve original value
                    updated_resource["schema"] = resource["schema"]

                save_json(
                    path=resource_path,
                    value=updated_resource,
                )

    # Update arguments resource metadata from environment variables
    arguments_resource["algorithm"] = algorithm_name
    arguments_resource["container"] = container_name

    # # TODO Validate argument outputs against algorithm interface

    # Save updated arguments resource
    save_json(
        path=f"{ARGUMENTS_PATH}/{algorithm_name}.{arguments_name}.json",
        value=arguments_resource,
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
