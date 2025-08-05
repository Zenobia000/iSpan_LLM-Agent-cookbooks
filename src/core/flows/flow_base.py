from functools import wraps

def flow(func):
    """A decorator to register a function as a flow."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Here, you could add logic to trigger the flow based on certain conditions,
        # schedule it, or log its execution. For now, it just calls the function.
        print(f"Triggering flow: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
