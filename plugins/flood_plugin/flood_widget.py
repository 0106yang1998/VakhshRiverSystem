import os

import geopandas as gpd
import rasterio
from rasterio.plot import plotting_extent

from PyQt5.QtCore import QDate, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from algorithms.flood import risk_assessment_6factors_entropy
from app.ui_hints import attach_hint, label_with_hint


class RasterCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.figure = Figure()
        super().__init__(self.figure)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def plot_risk_tif(self, tif_path, study_area_shp=None):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        with rasterio.open(tif_path) as src:
            arr = src.read(1).astype("float32")
            nodata = src.nodata
            if nodata is not None:
                arr[arr == nodata] = float("nan")
            extent = plotting_extent(src)

        im = ax.imshow(arr, extent=extent, origin="upper")
        self.figure.colorbar(im, ax=ax, fraction=0.036, pad=0.04, label="Flood Risk")

        if study_area_shp and os.path.exists(study_area_shp):
            gdf = gpd.read_file(study_area_shp)
            with rasterio.open(tif_path) as src:
                tif_crs = src.crs

            if gdf.crs is not None and tif_crs is not None and gdf.crs != tif_crs:
                gdf = gdf.to_crs(tif_crs)

            gdf.boundary.plot(ax=ax, linewidth=1.5)

        ax.set_title("Flood Risk Raster")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.grid(False)

        self.figure.tight_layout()
        self.draw()


class FloodWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.result_paths = None
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()

        title_label = QLabel("洪涝灾害风险评估")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        intro_label = QLabel(
            "动态气象因子按日尺度输入，静态地理因子默认自动读取。"
            "如静态数据缺失，系统会优先尝试自动补准备。"
        )
        intro_label.setWordWrap(True)

        self.run_btn = QPushButton("运行风险评估")
        self.load_btn = QPushButton("加载已有结果")
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        left_layout.addWidget(title_label)
        left_layout.addWidget(intro_label)
        left_layout.addWidget(self._build_input_group())
        left_layout.addWidget(self.run_btn)
        left_layout.addWidget(self.load_btn)
        left_layout.addWidget(self.log, 1)

        right_tabs = QTabWidget()
        self.raster_canvas = RasterCanvas()
        self.map_view = QWebEngineView()

        raster_tab = QWidget()
        raster_layout = QVBoxLayout(raster_tab)
        raster_layout.addWidget(self.raster_canvas)

        map_tab = QWidget()
        map_layout = QVBoxLayout(map_tab)
        map_layout.addWidget(self.map_view)

        right_tabs.addTab(raster_tab, "风险栅格")
        right_tabs.addTab(map_tab, "交互地图")

        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(right_tabs, 3)

        self.run_btn.clicked.connect(self.run_analysis)
        self.load_btn.clicked.connect(self.load_existing_results)

    def _build_input_group(self):
        group = QGroupBox("输入设置")
        form = QFormLayout(group)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())
        date_hint = "选择需要评估的日尺度气象数据日期，系统会自动匹配当天降雨和土壤湿度栅格。"
        attach_hint(self.date_input, date_hint)
        form.addRow(label_with_hint("目标日期:", date_hint), self.date_input)

        static_info = QLabel(
            "DEM、土地覆盖、研究区边界和河网默认从模块目录自动读取，"
            "无需每次重复输入。"
        )
        static_info.setWordWrap(True)
        static_hint = "静态数据固定读取，缺失时会尝试自动准备。"
        attach_hint(static_info, static_hint)
        form.addRow(label_with_hint("静态数据:", static_hint), static_info)

        return group

    def run_analysis(self):
        target_date = self.date_input.date().toString("yyyy-MM-dd")
        try:
            self.log.append(f"开始运行洪涝风险评估，目标日期: {target_date}")
            result = risk_assessment_6factors_entropy.run_risk_assessment(target_date=target_date)
            self.result_paths = result

            self.log.append(f"动态输入尺度: {result.get('dynamic_scale', 'unknown')}")
            if result.get("resolved_target_date"):
                self.log.append(f"实际使用日期: {result['resolved_target_date']}")

            self.log.append(f"降雨输入: {result['rain_path']}")
            self.log.append(f"土壤湿度输入: {result['soil_path']}")
            if result.get("static_actions"):
                self.log.append("静态数据处理: " + "；".join(result["static_actions"]))

            self.log.append(f"风险栅格已生成: {result['risk_tif']}")
            self.log.append(f"地图已生成: {result['map_html']}")

            self.display_results()
            self.log.append("洪涝风险评估完成。")
        except Exception as exc:
            self.log.append(f"[ERROR] {exc}")
            QMessageBox.critical(self, "错误", str(exc))

    def load_existing_results(self):
        try:
            base_dir = os.path.dirname(risk_assessment_6factors_entropy.__file__)
            risk_tif = os.path.join(base_dir, "outputs", "risk_6factors.tif")
            map_html = os.path.join(base_dir, "outputs", "flood_risk_map.html")
            study_area_shp = os.path.join(base_dir, "study_area.shp")

            if not os.path.exists(risk_tif):
                raise FileNotFoundError(f"未找到结果栅格: {risk_tif}")
            if not os.path.exists(map_html):
                raise FileNotFoundError(f"未找到结果地图: {map_html}")

            self.result_paths = {
                "risk_tif": risk_tif,
                "map_html": map_html,
                "study_area_shp": study_area_shp,
            }

            self.display_results()
            self.log.append("已加载已有结果。")
        except Exception as exc:
            self.log.append(f"[ERROR] {exc}")
            QMessageBox.critical(self, "错误", str(exc))

    def display_results(self):
        if not self.result_paths:
            return

        risk_tif = self.result_paths["risk_tif"]
        map_html = self.result_paths["map_html"]
        study_area_shp = self.result_paths.get("study_area_shp")

        self.raster_canvas.plot_risk_tif(
            tif_path=risk_tif,
            study_area_shp=study_area_shp,
        )

        if os.path.exists(map_html):
            self.map_view.load(QUrl.fromLocalFile(os.path.abspath(map_html)))
