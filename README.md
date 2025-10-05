# windows 工具箱

## 1.介绍

本项目是一款windows工具箱，采用插件化的设计，支持不同脚本插件的运行，项目采用python编写，支持执行`bat`、`py`、`exe`和`jar`插件运行。目前支持到win7 32位系统

## 2.安装

首先需要安装32位python 3.7,下载本项目

- 安装依赖 `pip install -r requirement.txt`
- 打包`pyinstaller main.spec`
- 进入到`dist`文件夹,双击`worktoolbox.exe`即可运行

## 3.插件介绍

插件一版分位2个文件，插件介绍文件`plugin.json`和插件执行文件，插件介绍文件`plugin.json`内容如下：

```json
{
  "name": "插件名称",
  "type": "插件类型，目前支持 bat，py，exe，jar",
  "description": "插件说明",
  "version": "插件版本",
  "entry": "插件入口文件名称，和插件执行文件保持一致",
  "args": [
    {
      "name": "参数名称",
      "label": "参数说明",
      "type": "参数类型，目前支持：folder，string，int，file，choice",
      "options": []
    }
  ]
}
```

## 4.