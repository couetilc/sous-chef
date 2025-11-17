from enum import Enum

class Intent(str, Enum):
    CLARIFY = "clarify"
    NEXT_STEP = "next_step"
    PREVIOUS_STEP = "previous_step"
    RESTART_RECIPE = "restart_recipe"
    REPAIR = "repair"