import tomllib, orjson, regex
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import TemplateError, StrictUndefined

class TomlProcessor:
    def __init__(self, context: dict = {}):
        self.context = context
        self.errors = []
        self.results = []

        self.env = SandboxedEnvironment(
            autoescape=True,
            keep_trailing_newline=False,
            undefined=StrictUndefined,
        )
        self.env.globals.clear()
        self.only_expression = regex.compile(r"\{\{.*?\}\}", regex.DOTALL)
        self.any_jinja = regex.compile(
            r"(\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\})", regex.DOTALL
        )
        self.after_equal = regex.compile(r"=(\s*)(\{\{.*?\}\})", regex.DOTALL)

    def _stream_blocks(self, file_path):
        with open(file_path, encoding="utf-8") as f:
            blk = []
            for line in f:
                if line.strip() == "" and blk:
                    yield "".join(blk)
                    blk = []
                else:
                    blk.append(line)
            if blk:
                yield "".join(blk)

    def _render_value(self, val: str):
        try:
            tmpl = self.env.overlay().from_string(val)
            result = tmpl.render(self.context)
        except (TemplateError, TypeError) as e:
            self.errors.append(f"Template error in {val!r}: {e}")
            return None

        if result is None or result.strip() == "":
            self.errors.append(f"Rendered value is empty for {val!r}")
            return None

        if self.only_expression.search(result):
            self.errors.append(f"Unrendered expression remains in {val!r}")
            return None

        return result

    def _render_values(self, obj):
        if isinstance(obj, str) and "{{" in obj:
            return self._render_value(obj)
        if isinstance(obj, dict):
            return {k: self._render_values(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._render_values(x) for x in obj]
        return obj

    def tools(self, filters=None, globals=None):
        filters = filters or []
        globals = globals or []

        # normalize filters
        if callable(filters):
            filters = [filters]
        elif isinstance(filters, (list, tuple)):
            if not all(callable(f) for f in filters):
                raise TypeError("All filter elements must be callable")
        else:
            raise TypeError("filters must be a callable or list/tuple of callables")

        # normalize globals
        if callable(globals):
            globals = [globals]
        elif isinstance(globals, (list, tuple)):
            if not all(callable(f) for f in globals):
                raise TypeError("All global elements must be callable")
        else:
            raise TypeError("globals must be a callable or list/tuple of callables")

        # register
        for f in filters:
            self.env.filters[f.__name__] = f
        for f in globals:
            self.env.globals[f.__name__] = f

        return self
        
    def _check_unrendered(self, obj):
        if isinstance(obj, str) and self.only_expression.search(obj):
            self.errors.append(f"Unrendered expression found: {obj}")
        if isinstance(obj, dict):
            for v in obj.values():
                self._check_unrendered(v)
        if isinstance(obj, list):
            for v in obj:
                self._check_unrendered(v)

    # merged process + main entry
    def run(self, file_path: str):
        self.errors.clear()
        self.results.clear()

        for blk in self._stream_blocks(file_path):
            raw = " ".join(line.strip() for line in blk.splitlines())

            for m in self.any_jinja.finditer(raw):
                if not self.only_expression.fullmatch(m.group(0)):
                    self.errors.append(
                        f"Only {{{{ }}}} expressions allowed, got: {m.group(0)}"
                    )

            for m in self.only_expression.finditer(raw):
                if not regex.search(r"=\s*" + regex.escape(m.group(0)), raw):
                    self.errors.append(
                        f"Jinja must appear only after '=': {m.group(0)}"
                    )

            safe_blk = self.after_equal.sub(r'=\1"""\2"""', blk)

            try:
                parsed = tomllib.loads(safe_blk)
            except Exception as e:
                self.errors.append(f"TOML parse error: {e}")
                continue

            for k, v in parsed.items():
                rendered = self._render_values(v)
                self._check_unrendered(rendered)

                if rendered is not None:
                    payload = (
                        rendered if isinstance(rendered, dict)
                        else {"value": rendered}
                    )
                    self.results.append({"_type": k, **payload})

        if self.errors:
            print(
                orjson.dumps(
                    {"status": "error", "errors": self.errors},
                    option=orjson.OPT_INDENT_2,
                ).decode()
            )
        else:
            print(
                orjson.dumps(
                    {"status": "ok", "data": self.results},
                    option=orjson.OPT_INDENT_2,
                ).decode()
            )
