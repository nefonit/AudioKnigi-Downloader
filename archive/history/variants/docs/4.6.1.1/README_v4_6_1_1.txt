AudioKnigi Downloader 4.6.1.1 — HiDPI hotfix
================================================

Исправлено предупреждение CustomTkinter:

CTkLabel Warning: Given image is not CTkImage but tkinter.PhotoImage

Теперь:
- системная иконка окна использует tkinter.PhotoImage;
- логотип в шапке использует CTkImage 52x52;
- маленький логотип статуса использует CTkImage 42x42;
- изображения корректно масштабируются на HighDPI 125/150/200%.

Функциональность 4.6.1 не изменена.
