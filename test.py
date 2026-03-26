from server import get_set_data, get_sets_html, get_set_binary

class MockDatabase:
    def __init__(self, set_rows, inventory_rows):
        self.set_rows = set_rows
        self.inventory_rows = inventory_rows
        self.call_count = 0
    
    def execute_and_fetch_all(self, query, params=None):
        self.call_count += 1
        if self.call_count == 1:
            return self.set_rows
        return self.inventory_rows
    
    def close(self):
        pass

def test_get_set_data():
    db = MockDatabase(
        set_rows=[("75192-1", "Millennium Falcon", 2017, "Star Wars")],
        inventory_rows=[
            ("3001", 11, 4),
            ("3002", 15, 2)
        ]
    )
    
    result = get_set_data(db, "75192-1")
    
    assert "75192-1" in result
    assert "Millennium Falcon" in result
    assert "3001" in result
    print("Test passed!")

def test_get_sets_html():
    class MockDatabase:
        def execute_and_fetch_all(self, query, params=None):
            return [("75192-1", "Millennium Falcon"), ("60001-1", "Fire Truck")]
        def close(self):
            pass
    
    db = MockDatabase()
    result = get_sets_html(db, "{CHARSET}{ROWS}", "utf-8")
    assert "75192-1" in result
    assert "Millennium Falcon" in result
    print("test_get_sets_html passed!")

def test_get_set_binary():
    class MockDatabase:
        def __init__(self):
            self.call_count = 0
        def execute_and_fetch_all(self, query, params=None):
            self.call_count += 1
            if self.call_count == 1:
                return [("75192-1", "Millennium Falcon", 2017, "Star Wars")]
            return [("3001", 11, 4)]
        def close(self):
            pass
    
    db = MockDatabase()
    result = get_set_binary(db, "75192-1")
    assert isinstance(result, bytes)
    print("test_get_set_binary passed!")

test_get_sets_html()
test_get_set_binary()
test_get_set_data()