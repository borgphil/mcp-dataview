from pathlib import Path
import yaml
from pydantic import ValidationError
from .models import ViewDefinition, Relationship

class MetadataError(RuntimeError):
    pass

class UniqueKeyLoader(yaml.SafeLoader):
    pass

def _construct_unique_mapping(loader: UniqueKeyLoader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise MetadataError(f"Duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping

UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping)

class MetadataRegistry:
    def __init__(self, directory: Path):
        self._views: dict[str, ViewDefinition] = {}
        self._load(directory)

    def _load(self, directory: Path) -> None:
        physical_views: set[str] = set()
        for path in sorted(directory.glob("*.yaml")):
            try:
                raw_view = yaml.load(path.read_text(), Loader=UniqueKeyLoader)
                if not isinstance(raw_view, dict):
                    raise MetadataError("View configuration must be a YAML mapping")
                raw_view["relationships"] = {
                    name: {**definition, "name": name}
                    for name, definition in raw_view.get("relationships", {}).items()
                }
                view = ViewDefinition.model_validate(raw_view)
            except (OSError, yaml.YAMLError, ValidationError) as exc:
                raise MetadataError(f"Invalid view configuration {path}: {exc}") from exc
            if view.name in self._views:
                raise MetadataError(f"Duplicate logical view: {view.name}")
            if view.sql_view in physical_views:
                raise MetadataError(f"Duplicate physical view: {view.sql_view}")
            physical_views.add(view.sql_view)
            if len(view.fields) != len(set(view.fields)):
                raise MetadataError(f"Duplicate field in {view.name}")
            for relationship in view.relationships.values():
                if relationship.to_view == view.name:
                    raise MetadataError(f"Self relationship is not allowed: {view.name}")
                for mapping in relationship.column_mappings:
                    if mapping.from_field not in view.fields:
                        raise MetadataError(f"Unknown source field {mapping.from_field}")
                source_fields = [mapping.from_field for mapping in relationship.column_mappings]
                target_fields = [mapping.to_field for mapping in relationship.column_mappings]
                if len(source_fields) != len(set(source_fields)) or len(target_fields) != len(set(target_fields)):
                    raise MetadataError(f"Duplicate relationship mapping in {view.name}.{relationship.name}")
            self._views[view.name] = view
        for view in self._views.values():
            for relationship in view.relationships.values():
                target = self.get_view(relationship.to_view)
                for mapping in relationship.column_mappings:
                    if mapping.to_field not in target.fields:
                        raise MetadataError(f"Unknown target field {mapping.to_field}")

    def get_view(self, name: str) -> ViewDefinition:
        try:
            return self._views[name]
        except KeyError as exc:
            raise MetadataError(f"View '{name}' is not available") from exc

    def get_relationship(self, source: str, target: str) -> Relationship:
        view = self.get_view(source)
        for relationship in view.relationships.values():
            if relationship.to_view == target:
                return relationship
        raise MetadataError(f"No configured relationship exists between {source} and {target}")

    def list_views(self) -> list[ViewDefinition]:
        return list(self._views.values())
