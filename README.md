# VakhshRiverSystem
瓦赫什河流域水文综合系统（Vakhsh River System）是一个基于 **Python + PyQt5** 构建的插件式桌面应用系统，面向流域水文、水资源、水灾害与遥感智能识别等业务场景，支持多模块集成、统一界面调度与专题功能扩展。

---

# 一、项目特点

- 基于 **PyQt5** 构建统一桌面界面
- 采用 **插件式架构**，各专题模块可独立开发
- 支持传统水文模型与 AI 推理模块融合
- 支持遥感影像、GIS、专题识别、优化配置等多类型任务
- 支持独立 Python 环境运行 AI 推理服务
- 便于扩展新的流域分析模块

---

# 二、项目目录结构

```
VakhshRiverSystem/
│
├─ algorithms/                         # 各业务算法模块
│  ├─ flood/                          # 洪涝风险评估
│  ├─ inundation_monitoring/          # 淹没区监测（UNet）
│  ├─ monitoring/                     # 水文监测
│  ├─ reservoir_estimation/           # 库区水量估算
│  ├─ routing/                        # 洪水演进与汇流
│  ├─ segformer_service/              # SegFormer推理服务（水体/积雪识别）
│  ├─ snow_state/                     # 积雪状态识别（GEE）
│  ├─ swe/                            # 雪水当量估算
│  ├─ warning/                        # 洪水预警监控
│  ├─ water_allocation/               # 水资源分配优化
│  └─ __init__.py
│
├─ app/                               # 主程序框架
│  ├─ __init__.py
│  ├─ base_plugin.py
│  ├─ main_window.py
│  └─ plugin_manager.py
│
├─ plugins/                           # 功能插件
│  ├─ flood_plugin/
│  ├─ inundation_monitoring_plugin/
│  ├─ monitoring_plugin/
│  ├─ reservoir_estimation_plugin/
│  ├─ routing_plugin/
│  ├─ segformer_plugin/
│  ├─ snow_state_plugin/
│  ├─ swe_plugin/
│  ├─ warning_plugin/
│  ├─ water_allocation_plugin/
│  └─ __init__.py
│
├─ output/                            # 输出目录
├─ config.py                          # 全局配置
├─ main.py                            # 程序入口
└─ README.md
```

---

# 三、系统架构说明

系统采用 **主系统 + 插件 + 算法模块** 的分层结构。

## 1. 主程序层

主程序位于：

```
main.py
app/
```

主要功能：

- 启动 Qt 应用
- 创建主窗口
- 初始化插件管理器
- 加载插件
- 管理标签页界面

---

## 2. 插件层

插件位于：

```
plugins/
```

每个插件对应一个系统功能模块。

插件负责：

- 构建界面
- 获取用户输入
- 调用算法模块
- 显示结果

插件结构示例：

```
plugins/example_plugin/
├─ plugin.py
└─ example_widget.py
```

插件接口示例：

```python
class ExamplePlugin:

    def name(self):
        return "模块名称"

    def widget(self):
        return ExampleWidget()
```

---

## 3. 算法层

算法模块位于：

```
algorithms/
```

主要负责：

- 数据处理
- 计算模型
- AI 推理
- 优化算法
- 输出结果

示例结构：

```
algorithms/module_name/
├─ __init__.py
├─ core.py
├─ model.py
└─ utils.py
```

算法层与 GUI 完全解耦。

---

## 4. AI 推理服务层

部分 AI 模型使用 **独立推理服务**。

例如：

```
algorithms/segformer_service/
```

主要特点：

- 独立 Python 环境
- GPU 推理
- 通过 subprocess 调用

---

## 5. GEE 云端识别层

新增的积雪状态识别模块采用“插件界面 + 算法封装 + GEE 云端导出”的接入方式：

```
plugins/snow_state_plugin/
algorithms/snow_state/
```

其中：

- 插件层负责日期、区域、数据源和导出参数录入
- 算法层负责 Earth Engine 初始化、积雪状态计算和导出任务提交
- 结果以 1-4 类积雪状态 GeoTIFF 导出到 Google Drive

---

# 四、系统模块

系统目前包含以下模块。

---

## 1 洪涝风险评估

插件目录：

```
plugins/flood_plugin/
```

算法目录：

```
algorithms/flood/
```

功能：

- 洪水风险识别
- GIS 分析
- 风险可视化

---

## 2 水文监测系统

插件目录：

```
plugins/monitoring_plugin/
```

算法目录：

```
algorithms/monitoring/
```

功能：

- 水位识别
- 光流测速
- 水文监测

---

## 3 库区水量估算

插件目录：

```
plugins/reservoir_estimation_plugin/
```

算法目录：

```
algorithms/reservoir_estimation/
```

功能：

- 库区面积估算
- 水库体积估算
- 结果 CSV 输出

---

## 4 洪水演进与汇流

插件目录：

```
plugins/routing_plugin/
```

算法目录：

```
algorithms/routing/
```

功能：

- 洪水传播模拟
- 汇流计算
- 河道分析

---

## 5 SegFormer 专题识别

插件目录：

```
plugins/segformer_plugin/
```

算法目录：

```
algorithms/segformer_service/
```

功能：

- 水体识别
- 积雪识别
- 语义分割

特点：

- 使用 SegFormer 模型
- 独立 AI 推理环境

---

## 6 积雪状态识别

插件目录：

```
plugins/snow_state_plugin/
```

算法目录：

```
algorithms/snow_state/
```

功能：

- 基于 GEE 的积雪物理状态识别
- 融合 Sentinel-1、Sentinel-2、MODIS 与 DEM 数据
- 支持 Google Drive 导出 GeoTIFF 结果
- 支持替换默认遥感数据源 ID

---

## 7 雪水当量估算

插件目录：

```
plugins/swe_plugin/
```

算法目录：

```
algorithms/swe/
```

功能：

- SWE 计算
- 雪区监测

---

## 8 淹没区监测

插件目录：

```
plugins/inundation_monitoring_plugin/
```

算法目录：

```
algorithms/inundation_monitoring/
```

功能：

- SAR 淹没区识别
- UNet 模型
- mask 叠加显示

---

## 9 水资源分配

插件目录：

```
plugins/water_allocation_plugin/
```

算法目录：

```
algorithms/water_allocation/
```

功能：

- NSGA-II 多目标优化
- 水资源调度
- 经济效益优化
- 公平性分析

---

## 10 洪水预警监控

插件目录：

```
plugins/warning_plugin/
```

算法目录：

```
algorithms/warning/
```

功能：

- 洪水预警
- 监控分析
- 决策辅助

---

# 五、运行环境

本项目实际使用两个 Conda 环境：

- `VakhshRiverSystem`：主程序环境，用于启动 PyQt5 桌面系统和大部分业务插件。
- `segformer`：SegFormer 独立推理环境，用于 `plugins/segformer_plugin` 调用水体/积雪语义分割服务。

依赖文件已导出到：

```text
requirements/
├─ environment-vakhsh.yml          # 主程序 Conda 环境
├─ environment-segformer.yml       # SegFormer Conda 环境
├─ requirements-vakhsh.txt         # 主程序 pip 依赖清单
└─ requirements-segformer.txt      # SegFormer pip 依赖清单
```

推荐优先使用 `environment-*.yml` 创建环境，因为它包含 Python 版本、Conda 包和 pip 包信息；`requirements-*.txt` 主要用于排查缺包或在已有环境中补装 pip 依赖。

## 1. 创建主程序环境

在项目根目录执行：

```bash
conda env create -f requirements/environment-vakhsh.yml
conda activate VakhshRiverSystem
python main.py
```

如果本机已经存在 `VakhshRiverSystem` 环境，可用下面命令更新：

```bash
conda activate VakhshRiverSystem
conda env update -n VakhshRiverSystem -f requirements/environment-vakhsh.yml
```

如果只是提示缺少某个 pip 包，可在项目根目录补装：

```bash
conda activate VakhshRiverSystem
pip install -r requirements/requirements-vakhsh.txt
```

## 2. 创建 SegFormer 独立环境

SegFormer 模块依赖旧版 `python=3.8`、`pytorch=1.10`、`mmcv-full=1.6.0` 和本项目内置的 MMSeg runtime，建议单独创建环境：

```bash
conda env create -f requirements/environment-segformer.yml
conda activate segformer
```

如果 Conda 创建过程中 `mmcv-full` 安装失败，可在项目根目录用本地 wheel 补装：

```bash
conda activate segformer
pip install algorithms/segformer_service/mmcv_full-1.6.0-cp38-cp38-win_amd64.whl
pip install -e algorithms/segformer_service/segformer_runtime
```

已有 `segformer` 环境时可更新：

```bash
conda activate segformer
conda env update -n segformer -f requirements/environment-segformer.yml
```

## 3. PyCharm 解释器设置

团队成员 clone 仓库后，需要在 PyCharm 中手动选择解释器：

- 主程序运行配置选择 `VakhshRiverSystem` 环境的 `python.exe`
- SegFormer 插件确认 `algorithms/segformer_service/service_config.py` 中的 `SEGFORMER_PYTHON` 指向本机 `segformer` 环境的 `python.exe`
- 不要用 `base` 环境运行本项目，否则可能出现 `cv2`、`geopandas`、`pymoo`、`mmcv` 等模块缺失

可用下面命令查看本机 Conda 环境路径：

```bash
conda info --envs
```

## 4. 维护者更新依赖文件

如果模块负责人新增了依赖，先在对应环境中安装并验证，再更新依赖文件。Windows PowerShell 中建议显式使用 UTF-8 输出：

```powershell
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
conda activate VakhshRiverSystem
pip freeze | Out-File -FilePath requirements/requirements-vakhsh.txt -Encoding utf8

conda activate segformer
pip freeze | Out-File -FilePath requirements/requirements-segformer.txt -Encoding utf8
```

Conda YAML 需要由项目维护者统一导出，并过滤本机 `prefix:` 路径，避免把个人电脑路径写进仓库。

```powershell
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
conda env export -n VakhshRiverSystem --no-builds | Where-Object { $_ -notmatch '^prefix:' } | Out-File -FilePath requirements/environment-vakhsh.yml -Encoding utf8
conda env export -n segformer --no-builds | Where-Object { $_ -notmatch '^prefix:' } | Out-File -FilePath requirements/environment-segformer.yml -Encoding utf8
```

---

# 六、系统启动

进入项目目录后执行：

```
python main.py
```

系统启动流程：

1. 初始化 Qt
2. 创建主窗口
3. 扫描插件
4. 加载模块
5. 启动系统

---

# 七、插件加载机制

插件加载流程：

1. main.py 启动程序
2. MainWindow 创建界面
3. PluginManager 扫描 plugins
4. 导入插件
5. 创建 widget
6. 添加标签页

核心文件：

```
app/plugin_manager.py
app/main_window.py
```

---

# 八、新模块接入

新增模块步骤：

### 1 新建算法模块

```
algorithms/new_module/
```

### 2 新建插件模块

```
plugins/new_module_plugin/
```

### 3 实现插件接口

```python
class ModulePlugin:

    class Plugin(BasePlugin):
        return "模块名称"

    def widget(self):
        return ModuleWidget()
```

---

# 九、GitHub 多人协同开发流程

本项目采用“稳定主线 + 集成分支 + 个人功能分支”的协作方式。所有模块负责人都应先在自己的分支完成算法和界面修改，再通过 GitHub Pull Request 合并，避免多人直接改同一条分支导致冲突。

## 1. 分支职责

- `main`：稳定版本分支，只放已经验证通过、可以演示或交付的代码。
- `dev/next`：日常集成分支，各模块功能先合并到这里统一联调。
- `feature/模块名-功能名`：模块负责人自己的开发分支，例如 `feature/swe-load-results`、`feature/flood-risk-levels`。
- `fix/模块名-问题名`：紧急修复分支，例如 `fix/water-allocation-pymoo-error`。

## 2. 第一次克隆项目

```bash
git clone <GitHub仓库地址>
cd VakhshRiverSystem
git checkout dev/next
conda activate VakhshRiverSystem
python main.py
```

如果本地已经有项目，不要重新复制文件夹，直接在原仓库里同步：

```bash
git fetch origin
git checkout dev/next
git pull origin dev/next
```

## 3. 每次开始开发前

先确认自己当前在哪个分支，并把 `dev/next` 更新到最新：

```bash
git status
git checkout dev/next
git pull origin dev/next
```

再从最新的 `dev/next` 创建自己的分支：

```bash
git checkout -b feature/模块名-功能名
```

示例：

```bash
git checkout -b feature/swe-result-view
```

## 4. 开发过程中提交代码

查看改动：

```bash
git status
git diff
```

只提交和自己模块相关的文件：

```bash
git add algorithms/模块名 plugins/模块名_plugin README.md
git commit -m "feat(模块名): 更新算法与界面显示"
```

常用提交信息前缀：

- `feat`：新增功能
- `fix`：修复问题
- `docs`：更新文档
- `refactor`：重构，不改变功能
- `chore`：配置、依赖、清理类修改

## 5. 推送到 GitHub 并发起 Pull Request

```bash
git push -u origin feature/模块名-功能名
```

然后在 GitHub 页面创建 Pull Request：

- base 分支选择 `dev/next`
- compare 分支选择自己的 `feature/...` 或 `fix/...`
- PR 标题写清楚模块和目的
- PR 描述里说明改了哪些算法、哪些界面、怎么验证

PR 合并前至少确认：

- `python main.py` 可以启动
- 自己负责的插件可以打开
- 按钮、输入框、图表、结果展示可以正常工作
- 没有提交 `__pycache__`、临时输出、大模型权重、个人路径配置

## 6. 开发中同步别人最新修改

如果自己开发了一段时间，别人已经合并了新代码，要把 `dev/next` 的最新内容同步到自己的分支：

```bash
git fetch origin
git checkout feature/模块名-功能名
git merge origin/dev/next
```

如果出现冲突，先打开冲突文件，保留双方需要的内容，确认程序能运行后再提交：

```bash
git status
git add 冲突文件路径
git commit -m "chore(模块名): resolve merge conflicts"
```

## 7. 合并后的本地清理

PR 合并后，本地切回集成分支并更新：

```bash
git checkout dev/next
git pull origin dev/next
```

确认自己的功能分支已经合并后，可以删除本地旧分支：

```bash
git branch -d feature/模块名-功能名
```

## 8. 不要直接提交的内容

以下内容通常不要提交到 GitHub：

- `output/` 下的临时运行结果
- `__pycache__/`、`.pyc`、`.ipynb_checkpoints/`
- 本机绝对路径配置，例如只在某台电脑存在的 `E:/...`
- 大体积模型权重、遥感原始数据、临时下载数据
- 账号、token、Google Earth Engine 私钥、云服务密钥

如果模块必须依赖大文件，请在 README 或模块说明中写清楚下载位置、文件名、放置目录，不要直接把大文件提交进仓库。

---

# 十、模块负责人更新算法与显示界面规范

每个业务模块通常由两部分组成：

- 算法代码：放在 `algorithms/模块名/`
- 插件界面：放在 `plugins/模块名_plugin/`

模块负责人更新功能时，优先只改自己负责的算法目录和插件目录。除非确实需要公共能力，否则不要随意修改 `main.py`、`app/main_window.py`、`app/plugin_manager.py`。

## 1. 推荐更新流程

1. 先在 `algorithms/模块名/` 中完成纯算法函数。
2. 用简单脚本或 Python 交互命令验证算法能独立运行。
3. 再到 `plugins/模块名_plugin/` 中更新按钮、输入框、结果展示。
4. 在插件里调用算法函数，把异常显示到界面日志或弹窗。
5. 启动 `python main.py`，验证主界面、插件标签页和结果展示。
6. 提交 PR，并在 PR 描述中写清验证步骤。

## 2. 算法模块怎么写

算法模块应尽量保持“可独立调用”，不要依赖界面控件。推荐结构：

```text
algorithms/example_module/
├─ __init__.py
├─ core.py
├─ config.py
└─ utils.py
```

`core.py` 示例：

```python
def run_example_analysis(input_path: str, threshold: float = 0.5) -> dict:
    if not input_path:
        raise ValueError("input_path 不能为空")

    # 在这里执行数据读取、模型推理或计算分析
    result_path = "output/example/result.png"

    return {
        "status": "success",
        "result_path": result_path,
        "summary": "分析完成",
    }
```

算法函数建议返回 `dict`，至少包含：

- `status`：运行状态
- `summary`：结果摘要
- `result_path` 或 `output_files`：输出文件路径
- `metrics`：关键指标
- `message`：给界面显示的说明

不要在算法层直接创建复杂 PyQt 控件；界面显示应由插件层负责。

## 3. 插件界面怎么写

每个插件目录至少包含：

```text
plugins/example_plugin/
├─ plugin.py
├─ plugin.json
└─ example_widget.py
```

`plugin.py` 示例：

```python
from app.base_plugin import BasePlugin
from .example_widget import ExampleWidget


class Plugin(BasePlugin):
    def name(self):
        return "示例模块"

    def order(self):
        return 999

    def widget(self):
        return ExampleWidget()
```

`example_widget.py` 中负责：

- 创建输入控件，例如文件选择、日期、阈值、下拉框
- 调用 `algorithms/模块名/` 中的算法函数
- 在 `QTextEdit`、`QLabel`、图表或图片区域展示结果
- 捕获异常并提示用户，不要让整个主程序崩溃

界面调用示例：

```python
from PyQt5.QtWidgets import QMessageBox, QPushButton, QTextEdit, QVBoxLayout, QWidget

from algorithms.example_module.core import run_example_analysis


class ExampleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.run_btn = QPushButton("运行分析")
        self.run_btn.clicked.connect(self.run_analysis)

        layout = QVBoxLayout(self)
        layout.addWidget(self.run_btn)
        layout.addWidget(self.log)

    def run_analysis(self):
        try:
            result = run_example_analysis(input_path="data/input.tif")
            self.log.append(result["summary"])
        except Exception as exc:
            self.log.append(f"[ERROR] {exc}")
            QMessageBox.critical(self, "运行失败", str(exc))
```

## 4. 算法和界面的连接原则

- 算法层只关心输入、计算、输出，不关心按钮和窗口。
- 插件层只负责收集用户输入、调用算法、展示结果。
- 长时间运行的任务应使用后台线程，避免界面卡死。
- 文件路径应来自用户选择、配置文件或模块默认目录，不要写死个人电脑路径。
- 输出结果优先放到模块自己的 `output/` 子目录，并避免提交临时结果。

## 5. 更新依赖时必须说明

如果模块新增第三方库，要同步更新文档，写清：

- 包名
- 推荐安装方式
- 是否需要独立 conda 环境
- 是否依赖 GPU、CUDA、GDAL、MMCV 等特殊组件

示例：

```bash
conda activate VakhshRiverSystem
pip install package-name
```

如果是 SegFormer 这类独立推理服务，应说明使用的独立环境，例如：

```text
algorithms/segformer_service/environment.yaml
```

并确认插件中的解释器路径配置正确。

## 6. 更新前后的自检清单

提交 PR 前请逐项检查：

- 当前分支不是 `main`
- 已从最新 `dev/next` 创建功能分支
- 只修改了自己负责的模块文件
- 新增算法可以单独运行
- 插件界面可以打开并显示结果
- 异常情况会在界面中提示
- `python main.py` 可以启动主程序
- `git status` 中没有无关临时文件
- PR 描述写明了测试步骤和已知限制

---

# 十一、项目说明

**VakhshRiverSystem**

瓦赫什河流域水文综合系统。

该系统整合：

- 水文监测
- 洪水模拟
- 水资源调度
- 遥感识别
- AI 模型分析

用于构建流域级综合分析平台。

---

# 十二、界面输入提示与格式说明（2026-04-07）

说明：

- 已在有输入项的界面中新增 `i` 说明符号（暗提示）。
- 鼠标悬停在 `i` 或输入控件上，可查看“输入内容 + 数据格式 + 示例”。
- 洪涝风险评估、洪水演进与汇流、雪水当量评估、洪水预警监控等模块当前以按钮/勾选操作为主，不涉及结构化数值录入格式。

## 1 水文监测（`plugins/monitoring_plugin`）

- 水位识别输入图像：单张 `jpg/png/bmp`，建议包含完整水尺刻度和清晰水线
- 流速识别输入视频：`mp4/avi/mov`，建议固定机位、画面稳定、河面纹理清晰
- 实测水面宽度：浮点数，单位 `m`，示例 `15.5`
- 实测河道水深：浮点数，单位 `dm`，示例 `2.3`
- 表面中心流速：浮点数，单位 `m/s`，示例 `1.28`

## 2 淹没区监测（`plugins/inundation_monitoring_plugin`）

- SAR 输入影像：`tif/tiff`（SAR=合成孔径雷达影像，非可见光照片），建议单波段灰度强度图
- 淹没区识别阈值：`0~1` 浮点数，示例 `0.5`

## 3 库区水量估算（`plugins/reservoir_estimation_plugin`）

- 水库名称：下拉选择
- 起始日期：日期格式 `yyyy-MM-dd`，示例 `2022-06-01`
- 结束日期：日期格式 `yyyy-MM-dd`，示例 `2022-06-07`

## 4 SegFormer 专题识别（`plugins/segformer_plugin`）

- 任务：下拉选择（`water` / `snow`）
- 设备：下拉选择（`cpu` / `cuda:0`）
- 图片路径：图像文件路径（`png/jpg/jpeg/bmp`，通过“选择输入图片”填写）

## 5 水资源分配（`plugins/water_allocation_plugin`）

- 选择月份：`1~12` 整数（下拉）
- 大坝当月可供水量：浮点数，单位 `百万m³`
- 区域当月可供其他水：浮点数，单位 `百万m³`
- 人口：浮点数，单位 `万人`
- 城镇化率：`0~100` 浮点数（百分比）
- 当地GDP：浮点数，单位 `亿元`
- 工业重复利用率：`0~100` 浮点数（百分比）
- 灌溉利用系数：`0~1` 浮点数
- 传输损耗率：`0~100` 浮点数（百分比）
- 生态保底水：浮点数，单位 `百万m³`
- 日ET0：浮点数，单位 `mm/天`（自动计算）
- 单机最大功率：浮点数，单位 `MW`
- 单机最大流量：浮点数，单位 `m³/s`
- 上网电价：浮点数，单位 `元/kWh`
- 作物类型：下拉选择
- 生育期：下拉选择
- 作物面积：浮点数，单位 `万亩`
- 作物产量：浮点数，单位 `kg/亩`
- 作物单价：浮点数，单位 `元/kg`
- 部门需水量：浮点数，单位 `百万m³`
- 整体经济权重：`0~1` 浮点数
- 降低缺水权重：`0~1` 浮点数
- 部门公平权重：`0~1` 浮点数
- 气象/水文数据源：`csv/nc` 文件路径或目录路径（可留空）
- 月初初始蓄水量：浮点数，单位 `亿m³`
- 种群规模：正整数
- 迭代代数：正整数
- ET0 气象参数（Rn/G/T/u2/es/ea/delta/gamma）：浮点数
