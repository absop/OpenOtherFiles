import os

import sublime
import sublime_plugin

import dctxmenu


user_settings = 'OpenOtherFiles.sublime-settings'

def plugin_loaded():
    def load_user_settings():
        OpenOtherFilesCommand.caption = settings.get('caption',
            'Open Other Files'
        )

    settings = sublime.load_settings(user_settings)
    settings.clear_on_change('caption')
    settings.add_on_change('caption', load_user_settings)

    load_user_settings()

    sublime.set_timeout(
        lambda: dctxmenu.register(__package__,
            OpenOtherFilesCommand.make_menu),
        500
    )

def plugin_unloaded():
    dctxmenu.deregister(__package__)


class OpenOtherFilesCommand(sublime_plugin.WindowCommand):
    caption = 'Open Other Files'
    command = 'open_other_files'

    @classmethod
    def make_menu(cls, view, event):
        if os.path.exists(view.file_name() or ""):
            index, items, paths = 0, [], []
            branch, leaf = os.path.split(view.file_name())
            for file in sorted(os.listdir(branch)):
                path = os.path.join(branch, file)
                if os.path.isfile(path) and file != leaf:
                    item = dctxmenu.item(file, cls.command, {'index': index})
                    items.append(item)
                    paths.append(path)
                    index += 1
            if len(items):
                cls.paths = paths
                return dctxmenu.fold_items(cls.caption, items)
        return None

    def run(self, index):
        file = self.paths[index]
        self.window.open_file(file)
