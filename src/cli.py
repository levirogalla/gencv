import typer


def main(name: str, age: int = None, teen: bool = True):
    """A simple command-line script."""
    print(f"Hello, {name}!")
    if age:
        print(f"You are {age} years old.")
    print(teen)


if __name__ == "__main__":
    typer.run(main)
