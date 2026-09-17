from audioknigi.core import safe_name
from audioknigi.models import Book, QueueItem, Track

assert safe_name("Книга.") == "Книга"
assert safe_name("NUL") == "_NUL"
assert safe_name("COM1.txt") == "_COM1.txt"

track = Track(index=1, title="01", file="https://example.invalid/a.mp3", duration=10.0)
book = Book(url="https://audioknigi.com.ua/test", title="Test", tracks=[track])
queue_item = QueueItem(url=book.url)

assert book["title"] == "Test"
assert book.tracks[0]["index"] == 1
assert queue_item.get("status") == "Ожидает"
assert not hasattr(queue_item, "output_mode")

print("safe_name Windows: OK")
print("Book/Track dataclasses: OK")
print("QueueItem dataclass: OK")
print("SELFTEST: OK")
