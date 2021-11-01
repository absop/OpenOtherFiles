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


class OpenFilePopupMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit, command):
        dir = os.path.dirname(self.view.file_name() or '')
        if not os.path.exists(dir):
            sublime.status_message('No such directory')
            return
        files = []
        for file in os.listdir(dir):
            path = os.path.join(dir, file)
            if os.path.isfile(path):
                files.append(file)

        def on_done(index):
            if index != -1:
                file = files[index]
                self.view.window().run_command(
                    command,
                    {
                        'file': os.path.join(dir, file)
                    }
                )
        self.view.show_popup_menu(files, on_done)


class OpenWithCommand(sublime_plugin.TextCommand):
    def is_visible(self):
        return self.view.file_name() is not None and (
            os.path.isfile(self.view.file_name()))

    def is_enabled(self):
        return self.view.file_name() is not None and (
            os.path.isfile(self.view.file_name()))

    def run(self, edit, command):
        self.view.window().run_command(
            command,
            {
                'file': self.view.file_name()
            })


class QuickOpenFileMenuCreater(menu.MenuCreater):
    def context_menu(self, event):
        filepath = self.view.file_name() or ''
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            return

        subitems = self.subitems
        for menu in self.menus:
            menu.items.clear()
        files = 0
        for file in os.listdir(dirpath):
            if self.exclude_file(file):
                continue
            path = os.path.join(dirpath, file)
            if os.path.isfile(path):
                ext = os.path.splitext(file)[1]
                if ext not in subitems:
                    ext = '.*'
                if ext not in subitems:
                    continue
                variables = {'file': file, 'path': path}
                for menu in subitems[ext]:
                    menu.add_item(file, variables)
                files += 1
                if files == self.files_limit:
                    break
        items = [menu.folded() for menu in self.menus if menu.items]
        if items and self.fold_subitems:
            return self.folded_item(self.caption, items)
        return items

    @classmethod
    def init(cls):
        file_exclude_patterns = settings.get('file_exclude_patterns', [])
        cls.exclude_file = pat2regex(file_exclude_patterns).match
        cls.caption = settings.get('caption', 'Quick Open File')
        cls.files_limit = settings.get('files_limit', 30)
        cls.fold_subitems = settings.get('fold_subitems', True)
        cls.subitems = {}
        cls.menus = []
        for obj in settings.get('subitems', []):
            caption = obj.get('caption', '')
            command = obj.get('command', '')
            args = obj.get('args', {})
            exts = obj.get('exts', [])
            if not (caption and command and args and exts):
                continue

            if isinstance(exts, str):
                exts = [exts]
            if not isinstance(exts, list):
                continue

            menu = Menu(caption, command, args)
            cls.menus.append(menu)
            for ext in exts:
                if ext not in cls.subitems:
                    cls.subitems[ext] = []
                cls.subitems[ext].append(menu)


class Menu:
    __slots__ = ['caption', 'command', 'args', 'items']

    def __init__(self, caption, command, args):
        self.caption = caption
        self.command = command
        self.args = args
        self.items = []

    def add_item(self, caption, variables):
        item = menu.MenuCreater.item(
            None, caption, self.command,
            {
                key: sublime.expand_variables(value, variables)
                for key, value in self.args.items()
            })
        self.items.append(item)

    def folded(self):
        return menu.MenuCreater.folded_item(None, self.caption, self.items)


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
