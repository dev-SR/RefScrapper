from rich.console import Console
console = Console()


def withLoader(cb, message="", spinner='aesthetic'):
    done = False
    returns = None
    with console.status(f"[bold yellow] {message}...", spinner=spinner) as s:
        while not done:
            returns = cb()
            done = True
    return returns


def withLoaderWithParam(cb, param, message="", spinner='aesthetic'):
    done = False
    returns = None
    with console.status(f"[bold yellow] {message}...", spinner=spinner) as s:
        while not done:
            returns = cb(*param)
            done = True
    return returns


def withLoaderWithParamNew(cb, param, message="", spinner='aesthetic'):
    done = False
    returns = None
    with console.status(f"[bold yellow] {message}...", spinner=spinner) as s:
        while not done:
            returns = cb(**param)
            done = True
    return returns
