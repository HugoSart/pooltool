from pooltool.utils.strenum import StrEnum


class GameType(StrEnum):
    """An Enum for supported game types

    Attributes:
        EIGHTBALL:
        NINEBALL:
        SINUQUINHA:
        THREECUSHION:
        SNOOKER:
        SUMTOTHREE:
    """

    EIGHTBALL = "Eight Ball"
    NINEBALL = "Nine Ball"
    SINUQUINHA = "Sinuquinha"
    THREECUSHION = "Three Cushion"
    SNOOKER = "Snooker"
    SUMTOTHREE = "Sum to Three"
