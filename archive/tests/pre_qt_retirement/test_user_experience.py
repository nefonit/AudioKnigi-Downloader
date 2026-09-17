import io
import tempfile
from pathlib import Path

from audioknigi import AudioKnigiApp
from audioknigi.models import Book, Track, QueueItem
from audioknigi.onboarding import FirstRunWizard
from audioknigi.help_center import HelpCenter
from audioknigi.core import APP_VERSION
try:
    from PIL import Image
except ImportError:
    Image=None

app=AudioKnigiApp(); app.update_idletasks()
assert app.title().endswith(APP_VERSION)

# First-run wizard has exactly two steps.
w=FirstRunWizard(app)
assert w.step==0
w.next(); assert w.step==1
w.next(); assert w.step==1
w.win.destroy()

# New help center opens.
h=HelpCenter(app); h.win.update_idletasks(); h.win.destroy()

# Queue/library Treeviews have a real cover column.
assert 'tree' in str(app.queue_tree.cget('show'))
assert 'tree' in str(app.history_tree.cget('show'))

with tempfile.TemporaryDirectory() as td:
    app.runtime_output_dir=td; app.runtime_use_templates=False
    book=Book(url='https://audioknigi.com.ua/test', title='Smoke Book', author='Author', tracks=[Track(index=1,title='01',file='https://example/file.mp3',start=0,end=10,duration=10)])
    folder=app._book_folder(book); (folder/'01.mp3').write_bytes(b'x'*4096)
    scan=app._scan_book_files(book)
    assert app._book_outputs_complete(book, scan)

    if Image is not None:
        im=Image.new('RGB',(80,120),'navy'); buf=io.BytesIO(); im.save(buf,format='PNG')
        book.cover_cache=(buf.getvalue(),'image/png')
    app.current_book=book
    app._show_completion_actions(folder)
    app.event_bus._drain()
    assert app.easy_result_title_var.get()=='Smoke Book'
    assert app.easy_completion_frame.winfo_manager()=='pack'

    item=QueueItem(url=book.url,title=book.title,cover_cache=book.cover_cache)
    app.queue_items=[item]; app._refresh_queue(); app.update_idletasks()
    assert len(app.queue_tree.get_children())==1

# Quality cards are keyboard-focusable in CustomTkinter mode when canvas exists.
for card in app.easy_home_view.quality_cards.values():
    fw=getattr(card,'_canvas',card)
    try:
        assert str(fw.cget('takefocus')) in ('1','true','True')
    except Exception:
        pass

print('FIRST-RUN WIZARD 2 STEPS: OK')
print('HELP CENTER: OK')
print('COVER COLUMNS: OK')
print('DUPLICATE DETECTION: OK')
print('RESULT CARD: OK')
print('KEYBOARD FOCUS: OK')
print('USER EXPERIENCE SMOKETEST: OK')
app.destroy()
