import typer


def compile_data():
    '''Compile data file to make sure it's formated properly.'''
    ...


def select_projects():
    '''Returns selected projects with selected point for each project to terminal.'''
    ...


def gen_resume():
    '''Generate resume.'''


def main(name: str, age: int = None, teen: bool = True):
    """A simple command-line script."""
    print(f"Hello, {name}!")
    if age:
        print(f"You are {age} years old.")
    print(teen)


if __name__ == "__main__":
    typer.run(main)
