from enum import StrEnum
from typing import List, Optional, Any, Union, Dict
from pydantic import BaseModel, Field, field_validator

class ActionType(StrEnum):
    ADD_TO_ORDER = "add_to_order"
    CLARIFY = "clarify"
    FINISH = "finish"

class Size(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class Modifications(BaseModel):
    remove: List[str] = Field(default_factory=list)
    add: List[str] = Field(default_factory=list)

class ComboDetails(BaseModel):
    side: Optional[str] = None
    side_size: Optional[Size] = None
    drink: Optional[str] = None
    drink_size: Optional[Size] = None

class LLMItem(BaseModel):
    name: str
    size: Optional[Size] = None
    quantity: int = 1
    modifications: Modifications = Field(default_factory=Modifications)
    combo_details: Optional[ComboDetails] = None

    @field_validator('modifications', mode='before')
    @classmethod
    def normalize_modifications(cls, v: Any) -> Any:
        if isinstance(v, list):
            merged = {"remove": [], "add": []}
            for item in v:
                if isinstance(item, dict):
                    rem = item.get("remove", [])
                    if isinstance(rem, list): merged["remove"].extend(rem)
                    elif isinstance(rem, str): merged["remove"].append(rem)
                    
                    add = item.get("add", [])
                    if isinstance(add, list): merged["add"].extend(add)
                    elif isinstance(add, str): merged["add"].append(add)
            return merged
        return v

class LLMResponse(BaseModel):
    action: ActionType
    items: List[LLMItem] = Field(default_factory=list)
    message_to_user: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response_text: str
    is_finished: bool = False
    order_summary: Optional[str] = None
    total_price: float = 0.0

class StartSessionResponse(BaseModel):
    session_id: str
    message: str