import argparse
import os
import json
import tempfile
import subprocess
from Scripts.bench_engine import run_benchmark

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('-t', '--threads',        required=True)
    args = p.parse_args()

    threads = int(args.threads)

    root = os.getcwd()
    engines = os.path.join(root, "Engines")
    configs = {}
    print(f"Using {threads} threads.")

    # get all engine config files
    config_files = [file for file in os.scandir(os.path.join(root, "Engines")) if file.is_file()]

    # create temporary working directory
    with tempfile.TemporaryDirectory() as path:
        os.chdir(path)

        for file in config_files:
            with open(file.path, "r") as f:
                data = f.read()
                obj = json.loads(data)

                # get engine info
                source = obj["source"]
                base_branch = obj["base"]
                makefile_path = obj["build"]["path"]
                name = source.split('/')[-1]

                print(f"Cloning [{name}/{base_branch}]...")
                os.chdir(path)
                subprocess.run(
                    ["git", "clone", source, "-b", base_branch, "--single-branch", "--depth", "1", "--quiet"],
                    stdout=subprocess.DEVNULL
                )

                try:
                    print("Compiling...")
                    make_path = os.path.join(path, name, makefile_path)
                    os.chdir(make_path)
                    subprocess.run(["make", "EXE=temp"], stdout=subprocess.DEVNULL)

                    print("Running Bench...")
                    try:
                        if os.name == 'nt':
                            exe = "temp.exe"
                        else:
                            exe = "./temp"

                        if not os.path.isfile(exe):
                            print("Couldn't Build!")
                            configs[file.name] = None
                            continue

                        result, bench = run_benchmark(exe, None, threads, 1)

                        print(f"BENCH: {bench}, NPS: {result}")
                        old_nps = str(obj["nps"])
                        obj["nps"] = int(result)
                        configs[file.name] = (old_nps, obj)
                    except Exception as error:
                        print(error)
                        print("Couldn't run bench!")
                        configs[file.name] = None
                except:
                    print("Couldn't compile!\n")
                    configs[file.name] = None
                    continue

                print("")

        os.chdir(root)

    # overwrite files and print summary
    for file in config_files:
        config = configs[file.name]
        if config != None:
            with open(file.path, "w") as f:
                nps = config[1]["nps"]
                print(f"{file.name.split('.')[0]: <12}: {config[0]: <8} -> {nps: >8}")
                f.write(json.dumps(config[1], indent=4))
        else:
            print(f"{file.name.split('.')[0]: <12}: An error occurred!")
