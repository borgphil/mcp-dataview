# View Configuration

Each logical view has exactly one YAML file under `config/views`. It declares `name`, trusted physical `sql_view`, descriptions, exposed fields, types, and outgoing relationships. Relationship map keys are their names; mappings support composite keys. Startup fails if a target view or mapped field is unknown.
