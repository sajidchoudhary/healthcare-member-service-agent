from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    aws_region: str = "ap-south-1"

    raw_data_dir: Path = BASE_DIR / "data" / "raw"
    processed_data_dir: Path = BASE_DIR / "data" / "processed"

    pdf_filename: str = "insurance_detail.pdf"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def pdf_path(self) -> Path:
        return self.raw_data_dir / self.pdf_filename

    @property
    def pages_json_path(self) -> Path:
        return self.processed_data_dir / "pages.json"

    @property
    def document_structure_path(self) -> Path:
        return self.processed_data_dir / "document_structure.json"

    @property
    def tables_json_path(self) -> Path:
        return self.processed_data_dir / "tables.json"


settings = Settings()