def test_import_engine_package():
    import engine
    assert hasattr(engine, "load_companies")
