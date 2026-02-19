class RuleInterface(ABC):
    def __init__(
        self, source_stage: Usd.Stage, package_root: str, destination_path: str, args: dict[str, Any]
    ) -> None: ...

    @abstractmethod
    def process_rule(self) -> str | None:
        """Execute the rule logic. Return a stage path to switch stages, or None."""
        ...

    @abstractmethod
    def get_configuration_parameters(self) -> list[RuleConfigurationParam]:
        """Return the configuration parameters for this rule."""
        ...

    def log_operation(self, message: str) -> None:
        """Append a message to the operation log."""
        ...

    def add_affected_stage(self, stage_identifier: str) -> None:
        """Record an identifier for a stage affected by this rule."""
        ...
