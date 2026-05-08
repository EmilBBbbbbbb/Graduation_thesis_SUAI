from pathlib import Path


def test_readme_exists_and_contains_title():
    p = Path("README.md")
    assert p.exists(), "README.md не найден"
    text = p.read_text(encoding="utf-8")
    assert "Прогнозирование" in text, "README.md, похоже, не содержит ожидаемого заголовка"


def test_essential_files_exist():
    required = [
        "app/main.py",
        "db/core.py",
        "parser/get_cost.py",
        "predict_model/LSTM.py",
        "predict_model/models",
    ]
    for rel in required:
        p = Path(rel)
        assert p.exists(), f"Ожидаемый файл/папка отсутствует: {rel}"


def test_model_pickle_files_nonempty():
    p = Path("predict_model/models")
    assert p.exists() and p.is_dir(), "Папка predict_model/models не найдена"
    pkls = list(p.glob("*.pkl"))
    assert len(pkls) > 0, "В папке predict_model/models не найдено pkl-артефактов"
    for f in pkls:
        assert f.stat().st_size > 0, f"Файл модели пустой: {f.name}"


def test_requirements_present():
    p = Path("requirements.txt")
    assert p.exists(), "requirements.txt не найден"
    lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]
    assert len(lines) > 0, "requirements.txt пуст или не содержит зависимостей"

