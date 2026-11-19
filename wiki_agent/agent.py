"""Standalone Wiki curation loop with verified publication as its completion gate."""
import inspect
import json
from pathlib import Path

from .integrations.model import ModelClient
from .schema import tool_schema
from .tools import core
from .tools.image_viewing import view_image
from .tools.wiki import read_wiki, search_wiki
from .tools.wiki_ingest import WikiIngestion
from .tools.wiki_prompts import GENERATION_PROMPT, PROJECT_SOURCE_PROMPT


def run_wiki_role(project, instruction, *, paper_path="paper/main.pdf",
                  project_evidence=False, source_paths=None, wiki_root=None,
                  force=False, complete_relations=True, model=None,
                  model_client=None, timeout=600, max_iterations=300,
                  on_progress=None):
    project = Path(project).resolve()
    client = model_client or ModelClient(model=model, timeout=timeout)
    curator = WikiIngestion(project, model=client, on_progress=on_progress)
    ctx = core.ToolContext(project, on_progress=on_progress)
    try:
        curator.assign(paper_path=paper_path, project_evidence=project_evidence,
                       source_paths=source_paths, wiki_root=wiki_root, force=force,
                       complete_relations=complete_relations)
        handlers = {f.__name__: core.ToolSpec(f.__name__, inspect.getdoc(f), f)
                    for f in (core.ls, core.read, core.write, core.edit,
                              search_wiki, read_wiki, view_image)}
        handlers.update({spec.name: spec for spec in curator.tools()})
        schemas = [tool_schema(spec) for spec in handlers.values()]
        skill = (Path(__file__).parent / "skills/wiki-curation/SKILL.md").read_text()
        messages = [{"role": "system", "content": "You are WikiAgent.\n" + skill
                     + "\n" + GENERATION_PROMPT + "\n" + PROJECT_SOURCE_PROMPT},
                    {"role": "user", "content": instruction + "\nAssignment:\n" + json.dumps({
                        "paper_path": paper_path, "project_evidence": project_evidence,
                        "source_paths": source_paths or [], "force": force,
                    }, ensure_ascii=False)}]
        for _ in range(max_iterations):
            response = client.complete(messages, schemas)
            if not response.tool_calls:
                curator.check_completion()
                return {**curator.receipt, "final": response.content,
                        "receipt_path": curator._display(curator.receipt_path)}
            messages.append({"role": "assistant", "content": response.content or None,
                             "tool_calls": [{"id": c.id, "type": "function", "function": {
                                 "name": c.name, "arguments": json.dumps(c.arguments)}}
                                 for c in response.tool_calls]})
            for call in response.tool_calls:
                try:
                    if call.name in {"write", "edit"}:
                        curator.validate_draft_write(call.arguments["path"])
                    result = handlers[call.name].handler(ctx, **call.arguments)
                except Exception as exc:
                    result = core.ToolResult(json.dumps({"error": str(exc)}), True)
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": result.output})
                if result.images:
                    messages.append({"role": "user", "content": result.images})
                if on_progress:
                    on_progress(call.name, {"is_error": result.is_error})
        raise RuntimeError("WikiAgent iteration budget exhausted; draft retained")
    except BaseException as exc:
        if not curator.receipt or curator.receipt.get("status") not in {"completed", "skipped"}:
            curator.wiki_abort(ctx, str(exc) or type(exc).__name__)
        raise
