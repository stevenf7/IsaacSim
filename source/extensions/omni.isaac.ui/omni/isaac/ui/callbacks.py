import carb
import sys
import os
import subprocess


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


def on_open_IDE_clicked(ext_path: str, file_path: str) -> None:
    """Opens the current directory and file in VSCode"""
    if sys.platform == "win32":
        carb.log_warn("windows not supported")
    else:
        try:
            import subprocess

            subprocess.run(["code", ext_path, file_path], check=True)
            # os.system("code " + ext_path + " " + file_path)
        except Exception:
            carb.log_warn(
                "Could not open in VSCode. See Troubleshooting help here: https://code.visualstudio.com/docs/editor/command-line#_common-questions"
            )


def on_open_folder_clicked(file_path: str) -> None:
    """Opens the current directory in a File Browser"""
    if sys.platform == "win32":
        # subprocess.Popen(['start', os.path.abspath(app_folder)], shell= True)
        carb.log_warn("windows not supported")
    else:
        try:
            subprocess.run(["xdg-open", os.path.abspath(file_path.rpartition("/")[0])], check=True)
        except Exception:
            carb.log_warn("could not open file browser")


def on_docs_link_clicked(doc_link: str) -> None:
    """Opens an extension's documentation in a Web Browser"""
    import webbrowser

    try:
        webbrowser.open(doc_link, new=2)
    except Exception:
        carb.log_warn("Could not open browswer with url: ", doc_link)
