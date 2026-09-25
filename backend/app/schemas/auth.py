from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, value: str) -> str:
        # Basic, explainable complexity rule rather than a fake "strength
        # meter": require at least one letter and one digit. Length (10+)
        # does more real work against brute force than special-character
        # rules, but we ask for both for defense in depth.
        has_letter = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)
        if not (has_letter and has_digit):
            raise ValueError("Password must contain at least one letter and one number")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
