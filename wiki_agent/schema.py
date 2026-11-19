import copy
import inspect
import types
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints
from .tools.core import ToolSpec

def tool_schema(spec: ToolSpec) -> dict[str, Any]:
    """Build an OpenAI function schema from a tool handler signature."""
    if spec.input_schema is not None:
        return {"type": "function", "function": {
            "name": spec.name, "description": spec.description,
            "parameters": copy.deepcopy(spec.input_schema)}}
    properties: dict[str, Any] = {}
    required: list[str] = []
    signature = inspect.signature(spec.handler)
    try:
        annotations = get_type_hints(spec.handler)
    except (NameError, TypeError):
        annotations = {}
    for name, parameter in list(signature.parameters.items())[1:]:
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            continue
        annotation = annotations.get(name, parameter.annotation)
        origin = get_origin(annotation)
        if origin in (Union, types.UnionType):
            non_none = [item for item in get_args(annotation) if item is not type(None)]
            annotation = non_none[0] if non_none else Any
            origin = get_origin(annotation)
        if origin is Literal:
            parameter_schema = {"type": "string", "enum": list(get_args(annotation))}
        elif annotation is bool:
            parameter_schema = {"type": "boolean"}
        elif annotation is int:
            parameter_schema = {"type": "integer"}
        elif annotation is float:
            parameter_schema = {"type": "number"}
        elif annotation in (dict, Any) or origin is dict:
            parameter_schema = {"type": "object"}
        elif origin in (list, tuple, set):
            item_type = get_args(annotation)[0] if get_args(annotation) else Any
            item_schema = {"type": (
                "object" if get_origin(item_type) is dict or item_type is dict
                else {int: "integer", float: "number", bool: "boolean"}.get(item_type, "string")
            )}
            parameter_schema = {"type": "array", "items": item_schema}
        else:
            parameter_schema = {"type": "string"}
        properties[name] = parameter_schema
        if parameter.default is inspect.Parameter.empty:
            required.append(name)
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return {"type": "function", "function": {"name": spec.name,
            "description": spec.description, "parameters": schema}}
