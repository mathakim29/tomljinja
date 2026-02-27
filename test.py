from tomlj2 import TomlProcessor

def double(x):
    return x * 2

processor = TomlProcessor({"username": "Alice", "user_age": 17})
processor.tools(filters=[double], globals=[double]).run("e.toml")