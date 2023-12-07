import common
import glob
import zipimport

def load_modules(path: str) -> list[type[common.Module]]:
    """
    Load all the modules within the `modules/` directory.

    Returns:
        list[type[module.Module]]: The module classes.
    """

    modules = []
    files = glob.glob(f"{path}*.zip")

    for file in files:
        try: 
            importer = zipimport.zipimporter(file)
            module = importer.load_module("module")
            if module.Module is not None:
                modules.append(module.Module)
        except Exception as e:
            print(f"Module Error for file {file}")
            print("======================")
            print(e)
            print("======================")
            print()

    return modules
