import os
import re

import sublime
import sublime_plugin

try:
    from dctxmenu import menu
except:
    sublime.error_message(
        f'The plugin `dctxmenu` is not installed, {__package__} stoped')
    raise


class ShowOpenFilesPopupMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        items = QuickOpenFileMenuCreater.create_menu_items_for_file(
            self.view.file_name()
        )
        window = self.view.window()
        def on_done(index):
            if index != -1:
                item = items[index]
                window.run_command(
                    item['command'],
                    item['args']
                )
        self.view.show_popup_menu(
            [item['caption'] for item in items],
            on_done
        )


class QuickOpenFileMenuCreater(menu.MenuCreater):
    def context_menu(self, event):
        if items := self.create_menu_items_for_file(self.view.file_name()):
            return self.folded_item(self.caption, items)

    @classmethod
    def create_menu_items_for_file(cls, file_path):
        if not os.path.exists(file_path or ""):
            return None
        items = []
        dir_path, leaf = os.path.split(file_path)
        for file in os.listdir(dir_path):
            if file == leaf or cls.exclude_file(file):
                continue
            path = os.path.join(dir_path, file)
            if os.path.isfile(path):
                ext = os.path.splitext(file)[1]
                if ext not in cls.menu_by_filetypes:
                    ext = '.*'
                variables = {'file': file, 'path': path}
                menu = cls.menu_by_filetypes[ext]
                caption = sublime.expand_variables(menu.caption, variables)
                command = menu.command
                args = {
                    argn: sublime.expand_variables(argv, variables)
                    for argn, argv in menu.args.items()
                }
                item = cls.item(None, caption, command, args)
                items.append(item)
                if len(items) == cls.files_limit:
                    break
        return items

    @classmethod
    def init(cls):
        file_exclude_patterns = settings.get('file_exclude_patterns', [])
        cls.exclude_file = pat2regex(file_exclude_patterns).match
        cls.caption = settings.get('caption', 'Quick Open File')
        cls.files_limit = settings.get('files_limit', 30)
        cls.menu_by_filetypes = {}
        for obj in settings.get('menu_by_filetypes', []):
            caption = obj.get('caption', '')
            command = obj.get('command', '')
            args = obj.get('args', {})
            exts = obj.get('exts', [])
            if caption and command and args and exts:
                menu = Menu(caption, command, args)
                if isinstance(exts, list):
                    for ext in exts:
                        cls.menu_by_filetypes[ext] = menu
                elif isinstance(exts, str):
                    cls.menu_by_filetypes[exts] = menu
        if '.*' not in cls.menu_by_filetypes:
            default_menu = Menu(
                'Open: ${file}',
                'open_file',
                {'file': '${path}'}
            )
            cls.menu_by_filetypes['.*'] = default_menu


class Menu:
    __slots__ = ['caption', 'command', 'args']

    def __init__(self, caption, command, args):
        self.caption = caption
        self.command = command
        self.args = args


def pat2regex(patterns):
    transtable = str.maketrans({
        '*': '.*',
        '.': '\\.',
        '?': '.'
    })

    def convert(pattern):
        return str.translate(pattern, transtable)

    try:
        regex = re.compile(f'^(?:{"|".join(map(convert, patterns))})$')
    except:
        regex = re.compile('.*')
        sublime.error_message(f'Invalid patterns: {patterns}')

    return regex


def reload_settings():
    global settings
    settings = sublime.load_settings('QuickOpenFile.sublime-settings')
    settings.add_on_change('caption', QuickOpenFileMenuCreater.init)
    QuickOpenFileMenuCreater.init()


def plugin_loaded():
    sublime.set_timeout_async(reload_settings)
    menu.register(__name__, QuickOpenFileMenuCreater)


def plugin_unloaded():
    settings.clear_on_change('caption')
    menu.remove(__name__)
