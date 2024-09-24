import os
import pickle
from opendatapy.datapackage import (
    load_resource_by_variable,
    load_resource,
    write_resource,
    load_run_configuration,
    write_run_configuration,
    load_algorithm,
    load_view,
    views_path,
    view_artefacts_path,
    ALGORITHM_DIR,
    get_algorithm_name,
)
from importlib.machinery import SourceFileLoader


# Datapackage is mounted at /datapackage in container definition
DATAPACKAGE_PATH = os.getcwd() + "/datapackage"


# Helpers


def execute():
    """Execute the specified run"""

    # Load requested execution parameters from env vars
    if "RUN" in os.environ:
        run_name = os.environ.get("RUN")
    else:
        raise ValueError("RUN environment variable missing")

    algorithm_name = get_algorithm_name(run_name)

    # Load run configuration
    run = load_run_configuration(run_name, base_path=DATAPACKAGE_PATH)

    # Load algorithm
    # TODO Validate run config variables against algorithm signature here
    algorithm = load_algorithm(algorithm_name, base_path=DATAPACKAGE_PATH)

    # Populate dict of key: value variable pairs to pass to function
    kwargs = {}

    for variable in run["data"]:
        variable_name = variable["name"]

        if "value" in variable:
            # Variable is a simple value
            kwargs[variable_name] = variable["value"]
        elif "resource" in variable:
            # Variable is a resource
            kwargs[variable_name] = load_resource_by_variable(
                run_name=run_name,
                variable_name=variable_name,
                base_path=DATAPACKAGE_PATH,
            )

    # Import algorithm module
    # Import as "algorithm_module" here to avoid clashing with any library
    # names (e.g. bindfit.py algorithm vs. bindfit library)
    algorithm_module = SourceFileLoader(
        "algorithm_module",
        ALGORITHM_DIR.format(
            base_path=DATAPACKAGE_PATH, algorithm_name=algorithm_name
        )
        + f"/{algorithm['code']}",
    ).load_module()

    # Execute algorithm with kwargs
    result: dict = algorithm_module.main(**kwargs)

    # Populate run configuration with outputs and save
    for variable in run["data"]:
        if variable["name"] in result.keys():
            # Update variable value or resource with algorithm output
            if "value" in variable:
                # Variable is a simple value
                variable["value"] = result[variable["name"]]
            elif "resource" in variable:
                # Variable is a resource, update the associated resource file
                # Get result resource
                updated_resource = result[variable["name"]].to_dict()

                # TODO: Validate updated_resource here - check it's a valid
                # resource of the type specified

                write_resource(
                    run_name=run_name,
                    resource=updated_resource,
                    base_path=DATAPACKAGE_PATH,
                )

    # TODO: Validate outputs against algorithm signature - make sure they are
    # the right types

    # Save updated run configuration
    write_run_configuration(run, base_path=DATAPACKAGE_PATH)


def view():
    """Render view in specified container"""
    view_name = os.environ.get("VIEW")
    run_name = os.environ.get("RUN")

    # Load view
    view = load_view(
        run_name=run_name, view_name=view_name, base_path=DATAPACKAGE_PATH
    )

    # Load associated resources
    resources = {}

    # TODO: Handle single resource case

    for resource_name in view["resources"]:
        # Load resource into TabularDataResource object
        resources[resource_name] = load_resource(
            run_name=run_name,
            resource_name=resource_name,
            base_path=DATAPACKAGE_PATH,
        )

    if view["specType"] == "matplotlib":
        # Import matplotlib module
        matplotlib_module = SourceFileLoader(
            "matplotlib_module",
            views_path.format(
                base_path=DATAPACKAGE_PATH,
                algorithm_name=get_algorithm_name(run_name),
            )
            + f"/{view['specFile']}",
        ).load_module()

        # Pass resources and execute
        fig = matplotlib_module.main(**resources)

        # Save figure
        figpath = (
            view_artefacts_path.format(
                base_path=DATAPACKAGE_PATH,
                run_name=run_name,
            )
            + f"/{view_name}"
        )

        print(f"Saving image at {figpath}.png")
        fig.savefig(f"{figpath}.png")

        print(f"Saving object at {figpath}.p")
        with open(f"{figpath}.p", "wb") as f:
            pickle.dump(fig, f)


if __name__ == "__main__":
    if "VIEW" in os.environ and "RUN" in os.environ:
        view()
    elif "RUN" in os.environ:
        execute()
    else:
        raise ValueError("RUN environment variable not provided")
