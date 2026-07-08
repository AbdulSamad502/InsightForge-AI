
from langchain.tools import BaseTool


class ToolRegistry:
    """
    Central registry for all AI agent tools.
    Adding a new tool = one register() call.
    The agent never needs to change.
    """
    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        cls._tools[tool.name] = tool

    @classmethod
    def get_all(cls) -> list[BaseTool]:
        return list(cls._tools.values())

    @classmethod
    def get(cls, name: str) -> BaseTool | None:
        return cls._tools.get(name)

    @classmethod
    def list_names(cls) -> list[str]:
        return list(cls._tools.keys())