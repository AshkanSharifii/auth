from dataclasses import (dataclass,
                         asdict)


# ----------------------------------------------------------------------------
@dataclass
class Base:
    """
    Base class for data models using dataclasses, providing serialization and deserialization methods.

    Methods:
        from_dict(cls, d: dict) -> 'Base':
            Class method to create an instance of the dataclass from a dictionary.

        to_dict(self) -> dict:
            Converts the dataclass instance into a dictionary.
    """

    @classmethod
    def from_dict(cls, d: dict) -> 'Base':
        return cls(**d)

    def to_dict(self) -> dict:
        return asdict(self)
