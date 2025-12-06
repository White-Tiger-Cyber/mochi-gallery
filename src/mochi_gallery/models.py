from pydantic import BaseModel, Field

class DesignDirectives(BaseModel):
    """
    AI must analyze the image structure before deciding placement.
    """
    composition_analysis: str = Field(description="Describe focal point and empty space.")
    text_color_hex: str = Field(description="Dominant text color (high contrast).")
    shadow_color_hex: str = Field(description="Shadow/Glow color.")
    shadow_strength: int = Field(description="Opacity of shadow (0-255).")
    y_position_percent: int = Field(description="Vertical center position (0-100).")
    font_vibe: str = Field(description="One of: 'handwritten', 'typewriter', 'serif', 'sans', 'bold'")
