from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

FieldType = Literal["string", "integer", "decimal", "date", "boolean"]
Cardinality = Literal["one_to_one", "one_to_many", "many_to_one", "many_to_many"]

class FieldDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    column: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    type: FieldType
    description: str

class RelationshipColumnMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_field: str
    to_field: str

class Relationship(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    to_view: str
    cardinality: Cardinality
    column_mappings: list[RelationshipColumnMapping] = Field(min_length=1)

class ViewDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    sql_view: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    description: str
    fields: dict[str, FieldDefinition] = Field(min_length=1)
    relationships: dict[str, Relationship] = Field(default_factory=dict)
