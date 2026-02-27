<h1>Toml Jinja 2</h1>

<p>How it works:</p>

e.toml
```toml
[user]
name = {{ username }}
age = {{ user_age }}

[greetings]
msg = {{ "Hello" + username }}
```

test.py
```python
from tomlj2 import TomlProcessor

def double(x):
    return x * 2

processor = TomlProcessor({"username": "Alice", "user_age": 17})
processor.tools(filters=[double], globals=[double]).run("e.toml")
```
Returns:
```json
{
  "status": "ok",
  "data": [
    {
      "_type": "user",
      "name": "Alice",
      "age": 17
    },
    {
      "_type": "greetings",
      "msg": "Hello, Alice!"
    }
  ]
}
```

## Notes
- The Jinja environment is sandboxed, no builtin global/filters are allowed, only ones defined in `.tools` function.

- Each block is processed individually (treated as a seperate toml file). This is intentional for use in a future project im working on 
