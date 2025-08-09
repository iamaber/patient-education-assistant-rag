import tempfile
from pathlib import Path

from data_ingestion.pipeline import build_default_pipeline
from data_ingestion.readers import load_drug_entries


def test_load_drug_entries():
    sample = Path(__file__).with_suffix("").parent / "fixtures" / "sample_medex.json"
    entries = load_drug_entries(sample)
    assert len(entries) >= 1
    assert "indications" in entries[0].dict()


def test_mini_pipeline():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # mock medex
        medex = tmp_path / "medex.json"
        medex.write_text(
            '[{"brand_name":"3-C Capsule","generic_name":"Cefixime Trihydrate","indications":"diabetes"}]'
        )

        # mock guideline
        guide_dir = tmp_path / "processed"
        guide_dir.mkdir()
        guide_dir.joinpath("diabetes.json").write_text(
            '[{"condition_tag":"diabetes","abstract":"Check HbA1c"}]'
        )

        from data_ingestion.config import settings as cfg

        cfg.update(
            {
                "drug_db_path": medex,
                "guideline_dir": guide_dir,
                "persist_directory": tmp_path / "chroma",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            }
        )

        pipeline = build_default_pipeline()
        pipeline.run()

        assert (tmp_path / "chroma").exists()
