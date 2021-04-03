# Open Other Files

## Feature
Dynamically generate context menus for you, allowing you to open other files in the current directory with the right mouse button.


## Installation
Before you install this plugin, you need to install my another plugin [dctxmenu](https://github.com/absop/dctxmenu)(**Dynamic Context Menu**). Because this plugin(**OpenOtherFiles**) uses **dctxmenu** to generate menus dynamically.

### !! Note:
Please make sure that **dtcxmenu** is installed correctly in a subdirectory called **dtcxmenu** in your package directory. If you're using `git clone`, you won't have this problem, but if you're using a browser to download it, you'll need to change the folder name.


## Settings

There is one and only one custom entry, named `caption`, which is a **title case** string shown on context menu.


## Examples
If you mainly use **English**
```json
{
    "caption": "Open Other Files"
}
```
![](image/en.png)

Or **Chinese**
```json
{
    "caption": "打开其他文件"
}
```
![](image/cn.png)
