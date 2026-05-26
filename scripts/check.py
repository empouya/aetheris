import subprocess

COMMANDS = [
    ["ruff", "format", "."],
    ["ruff", "check", "."],
    ["ruff", "format", "--check", "."],
    ["pyright"],
    ["pytest"],
]


def main() -> None:
    for command in COMMANDS:
        print(f"\n> {' '.join(command)}")
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
