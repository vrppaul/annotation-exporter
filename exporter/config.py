from dataclasses import dataclass, field
import os


@dataclass
class Config:
    CORRECT_USERNAME: str = field(init=False)
    CORRECT_PASSWORD: str = field(init=False)
    ROSSUM_TOKEN: str = field(init=False)
    BASE_ROSSUM_URL: str = field(init=False)
    RESULT_ROSSUM_URL: str = field(init=False)

    def __post_init__(self):
        self.CORRECT_USERNAME = os.environ["CORRECT_USERNAME"]
        self.CORRECT_PASSWORD = os.environ["CORRECT_PASSWORD"]
        self.ROSSUM_TOKEN = os.environ["ROSSUM_TOKEN"]
        self.BASE_ROSSUM_URL = os.environ["BASE_ROSSUM_URL"]
        self.RESULT_ROSSUM_URL = os.environ["RESULT_ROSSUM_URL"]
