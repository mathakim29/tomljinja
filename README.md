<h1>Toml Jinja 2</h1>

<p>How it works:</p>

```toml
[user]
name = {{ username }}
age = {{ user_age }}

[greetings]
msg = {{ "Hello" + username }}
```
```python
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
