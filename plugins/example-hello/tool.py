"""Example AetherOS plugin tool."""


def run(context: dict | None = None) -> dict:
    name = (context or {}).get("name", "Operator")
    return {"message": f"AetherOS acknowledges {name}. Systems nominal."}
