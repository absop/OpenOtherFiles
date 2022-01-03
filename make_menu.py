import os
import re

import sublime
import sublime_plugin

from sublime import expand_variables

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
    @classmethod
    def init(cls):
        file_exclude_patterns = settings.get('file_exclude_patterns', [])
        cls.exclude_file = pat2regex(file_exclude_patterns).match
        cls.caption = settings.get('caption', 'Quick Open File')
        cls.items_limit = settings.get('items_limit', 30)
        cls.folder_menus = []
        cls.file_menus = []

        for menu in settings.get('folder_menus', []):
            caption = menu.get('caption', '')
            command = menu.get('command', '')
            args = menu.get('args', {})
            if not (caption and command and args):
                continue
            cls.folder_menus.append((caption, command, args))

        for menu in settings.get('file_menus', []):
            caption = menu.get('caption', '')
            command = menu.get('command', '')
            args = menu.get('args', {})
            if not (caption and command and args):
                continue
            selector = Selector(menu.get('selector', []))
            cls.file_menus.append((caption, command, args, selector))

    def make_folder_menu(self, folder, variables):
        return self.folded_item(folder, [
            self.item(caption, command, expand_variables(args, variables))
            for caption, command, args in self.folder_menus
        ])

    def make_file_menu(self, file, variables):
        return self.folded_item(file, [
            self.item(caption, command, expand_variables(args, variables))
            for caption, command, args, selector in self.file_menus
                if selector.select(file)
        ])

    def context_menu(self, event):
        filepath = self.view.file_name() or ''
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            return
        items = []
        for file in os.listdir(dirpath):
            if self.exclude_file(file):
                continue
            path = os.path.join(dirpath, file)
            variables = {'file': file, 'path': path}
            if os.path.isfile(path):
                item = self.make_file_menu(file, variables)
            else:
                item = self.make_folder_menu(file, variables)
            items.append(item)
            if len(items) >= self.items_limit:
                break
        if items:
            return self.folded_item(self.caption, items)
        return items


class Selector:
    __slots__ = ['regex']

    def __init__(self, patterns):
        if not patterns:
            patterns = ["*"]
        elif isinstance(patterns, str):
            patterns = [patterns]
        self.regex = pat2regex(patterns)

    def select(self, name):
        return self.regex.match(name) is not None


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
