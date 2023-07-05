import os
import json
import tempfile
import subprocess

class Engine:
    path: str
    branch: str
    make_path: str

    def __init__(
            self,
            source: str,
            branch: str,
            make_path: bool
    ) -> None:
        self.source = source
        self.branch = branch
        self.make_path = make_path
        return

    def clone(self) -> None:
        subprocess.run(f"git clone {self.source} --single-branch --depth 1 --quiet", stdout=subprocess.DEVNULL)

if __name__ == "__main__":
    root = os.getcwd()
    engines = os.path.join(root, "Engines")
    configs = {}

    # get all engine config files
    config_files = [file for file in os.scandir(os.path.join(root, "Engines")) if file.is_file()]

    # create temporary working directory
    with tempfile.TemporaryDirectory() as path:
        os.chdir(path)

        for file in config_files:
            with open(file.path, "r") as f:
                data = f.read()
                obj = json.loads(data)
                engine = Engine(obj["source"], obj["base"], obj["build"]["path"])
                name = engine.source.split('/')[-1]

                print(f"Cloning [{name}]...")
                os.chdir(path)
                engine.clone()

                print("Compiling...")
                make_path = os.path.join(path, name, engine.make_path)
                os.chdir(make_path)
                subprocess.run("make EXE=temp", stdout=subprocess.DEVNULL)

                print("Running Bench...")
                try:
                    result = subprocess.run("temp.exe bench", stdout=subprocess.PIPE)
                    bench_line = result.stdout.decode('utf-8').strip().split('\n')[-1]
                    print(bench_line)
                    old_nps = str(obj["nps"])
                    nps = bench_line.split(' ')[-2]
                    obj["nps"] = int(nps)
                    configs[file.name] = [old_nps, nps, obj]
                except FileNotFoundError:
                    print("Couldn't run bench!")
                    configs[file.name] = None

                print("")
        os.chdir(root)

    # overwrite files and print summary
    for file in config_files:
        config = configs[file.name]
        if config != None:
            with open(file.path, "w") as f:
                print(f"{file.name.split('.')[0]: <12}: {config[0]: <8} -> {config[1]: >8}")
                # overwrite file
                f.write(json.dumps(config[2], indent=4))
        else:
            print(f"{file.name.split('.')[0]: 12>}: Could not get bench!")
