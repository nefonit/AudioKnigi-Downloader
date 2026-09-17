from audioknigi import AudioKnigiApp
from audioknigi.models import QueueItem

app=AudioKnigiApp()
app.queue_items=[QueueItem(url='https://audioknigi.com.ua/a',title='A'),QueueItem(url='https://audioknigi.com.ua/b',title='B')]
app._refresh_queue(); app.update_idletasks()
assert len(app.queue_tree.get_children())==2
assert app.queue_tree.bind('<B1-Motion>')
assert 'Перетащи книгу' in app.queue_drag_var.get()
app.queue_tree.selection_set('1')
app.queue_move_up()
assert app.queue_items[0].title=='B'
app.queue_tree.selection_set('0')
app.queue_toggle_priority()
assert app.queue_items[0].priority is True
app.queue_toggle_item_pause()
assert app.queue_items[0].paused is True
app.record_transfer_metrics(5*1024*1024,4)
app.update()
assert '5.00' in app.speed_var.get()
assert '4' in app.active_segments_var.get()
print('QUEUE VISUAL DND/REORDER/PRIORITY/PAUSE: OK')
print('SPEED GRAPH METRICS: OK')
print('QUEUE/UI SMOKETEST: OK')
app.destroy()
