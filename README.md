# Mozbitbar

Mozbitbar is a wrapper around Bitbar's [Testdroid](https://github.com/bitbar/testdroid-api-client-python) API client for Python2.

Mozbitbar implements a subset of tasks that Testdroid supports, but aims to make the process of starting Bitbar tasks easier and better defined through the use of _recipes_.


## Installation

Currently, installation via `setuptools` is supported.

```
$ python setup.py install
```

If working on the code, please use

```
$ python setup.py develop
```

## Invocation

If installed using `setuptools`, Mozbitbar can be started as command-line tool:

```
$ mozbitbar --recipe <path_to_recipe>
```

If the repository is cloned but not installed, it is still possible to invoke Mozbitbar:

```
$ export PYTHONPATH=.
$ python mozbitbar/main.py --recipe <full_path_to_recipe>
```

### credentials

A valid set of credentials is required to use Mozbitbar. These are supplied from Bitbar.

Mozbitbar supports two methods of setting user credentials.

**Environment Variables** (preferred):

Upon invocation, mozbitbar will search through user's environment variables and attempt to set required credentials. For more information on how to format the environment variables, please refer to [Bitbar Official Documentation](https://github.com/bitbar/testdroid-api-client-python).

The minimum required set of credentials are:

````
((`username` and `password`) or (`apikey`)) and (`url`)
````

**Keyword Arguments**:

This is an insecure method as it requires sensitive credentials to be written in the recipe. However, this may be a useful method if the recipe is generated on the fly and/or is never committed to a repository.

## Usage

Define a recipe under `mozbitbar/recipes` directory.

Recipes must be in valid YAML format. If uncertain, first step is to ensure the recipe can be parsed by PyYAML.

An example of the expected format of the recipe can be seen below:

````
- action: create_project
  arguments:
    name: hello_world
    type: DEFAULT
````

There are specific rules that must be followed in order to create a valid Mozbitbar recipe, which will be covered below.

## Defining a recipe

### action

`action` is a top level command in the recipe. Using action, the recipe writer is able to instruct Mozbitbar to call specific actions implemented in the module.

Therefore the `action` command must map to a valid action in the BitbarProject object.

### arguments

`arguments` is the subcommand in the recipe. It must be preceded by an `action` command and is used to pass arguments into the Python method that implements the action.

For example. in the above example, the `create_project` action requires two arguments to be passed: `name`, which is the project name, and `type` which is the project type.

### arguments themselves

Following the `arguments` subcommand is the list of arguments to be passed into the method. These are key:value pairs and the key must correspond to the parameter name.

## Other Notes

It is _highly_ recommended to use a virtual environment with Mozbitbar.

## Tests

Tests are written using `pytest` framework, in addition to specific components from the built-in `unittest` framework.

Pytest permits a concise, power yet easy-to-read test framework, and its features such as `parametrize` and `monkeypatching` are heavily utilized.

Unittest offers the built-in `mock` feature to patch some objects on an ad-hoc basis.

### running tests

Invoke tests as follows:

````
$ pytest
````

For additional parameters that pytest supports, please refer to the pytest usage guide.

### coverage tool

Coverage tool is available once the following command is run:

````
$ pytest --cov-report html --cov=mozbitbar tests/
````

Once all tests complete and are passing, an HTML-formatted report is available to view at `mozbitbar/htmlcov/index.html`.