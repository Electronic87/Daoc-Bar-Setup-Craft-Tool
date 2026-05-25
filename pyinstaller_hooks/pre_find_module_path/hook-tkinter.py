"""Allow PyInstaller to find tkinter in the bundled Codex Python runtime."""


def pre_find_module_path(hook_api):
    return None
