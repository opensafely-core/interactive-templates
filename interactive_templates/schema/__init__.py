from attrs import define


def interactive_schema(name):
    def decorator(cls):
        cls = define(slots=False)(cls)
        cls.analysis_name = name
        return cls

    return decorator


@define
class Codelist:
    label: str
    slug: str
    type: str  # noqa: A003
    description: str | None = None

    # the relative path the codelist was downloaded to
    path: str | None = None
