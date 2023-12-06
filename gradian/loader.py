import glob
from . import module
import zipimport

def load_modules() -> list[type[module.Module]]:
    """
    Load all the modules within the `modules/` directory.

    Returns:
        list[type[module.Module]]: The module classes.
    """

    modules = []
    files = glob.glob("./modules/*.zip")

    for file in files:
        try: 
            importer = zipimport.zipimporter(file)
            module = importer.load_module("entry")
            if module.Module is not None:
                modules.append(module.Module)
        except: pass

    return modules
