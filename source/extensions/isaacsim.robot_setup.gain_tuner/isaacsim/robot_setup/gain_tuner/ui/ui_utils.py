import carb


def on_copy_to_clipboard(to_copy: str) -> None:
    """
    Copy text to system clipboard
    """
    try:
        import pyperclip
    except ImportError:
        carb.log_warn("Could not import pyperclip.")
        return
    try:
        pyperclip.copy(to_copy)
    except pyperclip.PyperclipException:
        carb.log_warn(pyperclip.EXCEPT_MSG)
        return
