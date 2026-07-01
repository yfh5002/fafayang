# -*- coding: utf-8 -*-
"""
HJSYSTEM PyQt6 Desktop Application
完整的桌面端元器件核价系统
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QLabel,
    QDialog, QFormLayout, QMessageBox, QFileDialog, QHeaderView,
    QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox, QSplitter,
    QStatusBar, QToolBar, QMenuBar, QMenu, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon, QFont, QKeySequence, QShortcut

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import init_db, SessionLocal
from backend.crud import (
    get_components, get_component, create_component, update_component,
    delete_component, delete_all_components, get_component_count,
    get_components_by_ids, create_log_entry, get_logs, clear_logs
)
from backend.schemas import ComponentCreate, ComponentUpdate, LogCreateRequest
from backend.excel_handler import import_from_excel, export_to_excel


class ComponentDialog(QDialog):
    """Add/Edit Component Dialog"""
    
    def __init__(self, parent=None, component=None):
        super().__init__(parent)
        self.component = component
        self.setWindowTitle("编辑元器件" if component else "新增元器件")
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入元器件名称")
        layout.addRow("名称 *:", self.name_input)
        
        # Model
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("请输入型号及规格")
        layout.addRow("型号及规格:", self.model_input)
        
        # Quantity
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 999999)
        self.quantity_input.setValue(1)
        layout.addRow("数量:", self.quantity_input)
        
        # Unit Price
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 9999999)
        self.price_input.setDecimals(2)
        self.price_input.setValue(0)
        layout.addRow("单价:", self.price_input)
        
        # Remarks
        self.remarks_input = QLineEdit()
        self.remarks_input.setPlaceholderText("请输入备注信息")
        layout.addRow("备注:", self.remarks_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
        """)
        self.btn_save.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addRow(btn_layout)
        
        # Load data if editing
        if self.component:
            self.load_data()
    
    def load_data(self):
        self.name_input.setText(self.component.name)
        self.model_input.setText(self.component.model or "")
        self.quantity_input.setValue(self.component.quantity)
        self.price_input.setValue(self.component.unit_price)
        self.remarks_input.setText(self.component.remarks or "")
    
    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'model': self.model_input.text().strip(),
            'quantity': self.quantity_input.value(),
            'unit_price': self.price_input.value(),
            'remarks': self.remarks_input.text().strip()
        }


class LogDialog(QDialog):
    """Operation Logs Dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("操作日志")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_logs()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.load_logs)
        toolbar.addWidget(self.btn_refresh)
        
        self.btn_clear = QPushButton("清空日志")
        self.btn_clear.setStyleSheet("color: #dc2626;")
        self.btn_clear.clicked.connect(self.clear_logs)
        toolbar.addWidget(self.btn_clear)
        
        toolbar.addStretch()
        
        self.lbl_count = QLabel("共 0 条")
        toolbar.addWidget(self.lbl_count)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "时间", "操作", "详情", "元器件", "IP地址"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
    
    def load_logs(self):
        db = SessionLocal()
        try:
            logs = get_all_logs(db)
            self.table.setRowCount(len(logs))
            self.lbl_count.setText(f"共 {len(logs)} 条")
            
            for row, log in enumerate(logs):
                created_at_str = log.created_at.strftime("%Y/%m/%d %H:%M:%S") if log.created_at else ""
                self.table.setItem(row, 0, QTableWidgetItem(created_at_str))
                self.table.setItem(row, 1, QTableWidgetItem(log.action))
                self.table.setItem(row, 2, QTableWidgetItem(log.details or ""))
                self.table.setItem(row, 3, QTableWidgetItem(log.component_name or ""))
                self.table.setItem(row, 4, QTableWidgetItem(log.user_ip or ""))
        finally:
            db.close()
    
    def clear_logs(self):
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有日志吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                count = clear_logs(db)
                create_log_entry(
                    db,
                    LogCreateRequest(action="清空日志", details=f"清空 {count} 条日志"),
                    "", ""
                )
                QMessageBox.information(self, "成功", f"已清空 {count} 条日志")
                self.load_logs()
            finally:
                db.close()


class MainWindow(QMainWindow):
    """Main Application Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HJSYSTEM 元器件核价系统 v2.0")
        self.setMinimumSize(1400, 900)
        
        # Initialize database
        init_db()
        
        # Selected items for export
        self.selected_ids = set()
        
        self.setup_ui()
        self.load_data()
        self.setup_auto_refresh()
    
    def setup_ui(self):
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("元器件核价系统")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1a1a1a;
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索名称、型号、备注...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.on_search)
        toolbar.addWidget(self.search_input)
        
        toolbar.addStretch()
        
        # Action buttons
        btn_style = """
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                margin: 0 5px;
            }
        """
        
        self.btn_add = QPushButton("+ 新增元器件")
        self.btn_add.setStyleSheet(btn_style + """
            QPushButton { background-color: #4f46e5; color: white; }
            QPushButton:hover { background-color: #4338ca; }
        """)
        self.btn_add.clicked.connect(self.add_component)
        toolbar.addWidget(self.btn_add)
        
        self.btn_import = QPushButton("↑ 导入数据库")
        self.btn_import.setStyleSheet(btn_style + """
            QPushButton { background-color: #059669; color: white; }
            QPushButton:hover { background-color: #047857; }
        """)
        self.btn_import.clicked.connect(self.import_data)
        toolbar.addWidget(self.btn_import)
        
        self.btn_export = QPushButton("↓ 备份数据库")
        self.btn_export.setStyleSheet(btn_style + """
            QPushButton { background-color: #6b7280; color: white; }
            QPushButton:hover { background-color: #4b5563; }
        """)
        self.btn_export.clicked.connect(self.export_data)
        toolbar.addWidget(self.btn_export)
        
        self.btn_logs = QPushButton("操作日志")
        self.btn_logs.setStyleSheet(btn_style + """
            QPushButton { background-color: #0891b2; color: white; }
            QPushButton:hover { background-color: #0e7490; }
        """)
        self.btn_logs.clicked.connect(self.show_logs)
        toolbar.addWidget(self.btn_logs)
        
        self.btn_clear = QPushButton("清空全部")
        self.btn_clear.setStyleSheet(btn_style + """
            QPushButton { background-color: #dc2626; color: white; }
            QPushButton:hover { background-color: #b91c1c; }
        """)
        self.btn_clear.clicked.connect(self.clear_all)
        toolbar.addWidget(self.btn_clear)
        
        layout.addLayout(toolbar)
        
        # Stats bar
        stats_layout = QHBoxLayout()
        self.lbl_total = QLabel("元器件数据量: 0")
        self.lbl_total.setStyleSheet("font-weight: bold; color: #1a1a1a;")
        stats_layout.addWidget(self.lbl_total)
        
        stats_layout.addStretch()
        
        self.lbl_selected = QLabel("已选中: 0")
        self.lbl_selected.setStyleSheet("font-weight: bold; color: #4f46e5;")
        stats_layout.addWidget(self.lbl_selected)
        
        layout.addLayout(stats_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "选择", "序号", "名称", "型号及规格", "数量", "单价", "小计", "备注"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
            }
            QHeaderView::section {
                background-color: #4f46e5;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)
        
        # Set column widths
        self.table.setColumnWidth(0, 50)   # Select
        self.table.setColumnWidth(1, 60)   # Sequence
        self.table.setColumnWidth(2, 200)  # Name
        self.table.setColumnWidth(3, 300) # Model
        self.table.setColumnWidth(4, 80)  # Quantity
        self.table.setColumnWidth(5, 100) # Price
        self.table.setColumnWidth(6, 100) # Subtotal
        
        layout.addWidget(self.table)
        
        # Bottom toolbar
        bottom_layout = QHBoxLayout()
        
        self.btn_delete_selected = QPushButton("删除选中")
        self.btn_delete_selected.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #b91c1c; }
        """)
        self.btn_delete_selected.clicked.connect(self.delete_selected)
        bottom_layout.addWidget(self.btn_delete_selected)
        
        self.btn_export_selected = QPushButton("导出选中")
        self.btn_export_selected.setStyleSheet("""
            QPushButton {
                background-color: #4f46e5;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4338ca; }
        """)
        self.btn_export_selected.clicked.connect(self.export_selected)
        bottom_layout.addWidget(self.btn_export_selected)
        
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def setup_auto_refresh(self):
        """Setup auto refresh timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(5000)  # Refresh every 5 seconds
    
    def load_data(self):
        """Load data from database"""
        db = SessionLocal()
        try:
            search_text = self.search_input.text().strip()
            components, total = get_components(
                db, 
                skip=0, 
                limit=1000, 
                search=search_text
            )
            
            self.table.setRowCount(len(components))
            self.lbl_total.setText(f"元器件数据量: {total}")
            
            for row, comp in enumerate(components):
                # Checkbox
                checkbox = QCheckBox()
                checkbox.setChecked(str(comp.id) in self.selected_ids)
                checkbox.stateChanged.connect(lambda state, cid=comp.id: self.on_select_changed(cid, state))
                self.table.setCellWidget(row, 0, checkbox)
                
                # Data
                self.table.setItem(row, 1, QTableWidgetItem(str(comp.sequence or row + 1)))
                self.table.setItem(row, 2, QTableWidgetItem(comp.name))
                self.table.setItem(row, 3, QTableWidgetItem(comp.model or ""))
                self.table.setItem(row, 4, QTableWidgetItem(str(comp.quantity)))
                self.table.setItem(row, 5, QTableWidgetItem(f"{comp.unit_price:.2f}"))
                self.table.setItem(row, 6, QTableWidgetItem(f"{comp.subtotal:.2f}"))
                self.table.setItem(row, 7, QTableWidgetItem(comp.remarks or ""))
                
                # Store ID in first column's data
                self.table.item(row, 1).setData(Qt.ItemDataRole.UserRole, comp.id)
        finally:
            db.close()
    
    def on_select_changed(self, comp_id, state):
        """Handle selection change"""
        if state == Qt.CheckState.Checked.value:
            self.selected_ids.add(str(comp_id))
        else:
            self.selected_ids.discard(str(comp_id))
        self.lbl_selected.setText(f"已选中: {len(self.selected_ids)}")
    
    def on_search(self):
        """Handle search"""
        self.load_data()
    
    def add_component(self):
        """Add new component"""
        dialog = ComponentDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "警告", "名称不能为空")
                return
            
            db = SessionLocal()
            try:
                component = create_component(db, ComponentCreate(**data))
                create_log_entry(
                    db,
                    LogCreateRequest(
                        action="新增",
                        details=f"新增元器件: {data['name']}",
                        component_name=data['name'],
                        component_model=data['model']
                    ),
                    "", ""
                )
                self.status_bar.showMessage(f"已添加: {data['name']}", 3000)
                self.load_data()
            finally:
                db.close()
    
    def import_data(self):
        """Import from Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return
        
        try:
            components, skipped = import_from_excel(file_path)
            if not components:
                QMessageBox.warning(self, "警告", "未找到有效数据")
                return
            
            db = SessionLocal()
            try:
                from backend.crud import bulk_create_components
                imported, duplicates = bulk_create_components(db, components)
                create_log_entry(
                    db,
                    LogCreateRequest(
                        action="导入",
                        details=f"导入Excel文件，成功 {imported} 条，跳过 {skipped} 条空行，去重 {duplicates} 条"
                    ),
                    "", ""
                )
                QMessageBox.information(
                    self, "成功", 
                    f"导入完成!\n成功: {imported} 条\n跳过空行: {skipped} 条\n去重: {duplicates} 条"
                )
                self.load_data()
            finally:
                db.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def export_data(self):
        """Export to Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "元器件报价清单.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        
        try:
            db = SessionLocal()
            try:
                components = get_all_components(db)
                export_to_excel(components, file_path, "元器件报价清单")
                create_log_entry(
                    db,
                    LogCreateRequest(action="导出", details=f"导出全部数据到: {file_path}"),
                    "", ""
                )
                QMessageBox.information(self, "成功", f"已导出到:\n{file_path}")
            finally:
                db.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def export_selected(self):
        """Export selected items"""
        if not self.selected_ids:
            QMessageBox.warning(self, "警告", "请先选择要导出的数据")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "选中元器件清单.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        
        try:
            db = SessionLocal()
            try:
                ids = [int(id) for id in self.selected_ids]
                components = get_components_by_ids(db, ids)
                export_to_excel(components, file_path, "选中元器件清单")
                create_log_entry(
                    db,
                    LogCreateRequest(action="导出", details=f"导出选中 {len(ids)} 条到: {file_path}"),
                    "", ""
                )
                QMessageBox.information(self, "成功", f"已导出到:\n{file_path}")
            finally:
                db.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def delete_selected(self):
        """Delete selected items"""
        if not self.selected_ids:
            QMessageBox.warning(self, "警告", "请先选择要删除的数据")
            return
        
        reply = QMessageBox.question(
            self, "确认", 
            f"确定要删除选中的 {len(self.selected_ids)} 条数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        db = SessionLocal()
        try:
            count = 0
            for id_str in self.selected_ids:
                comp = get_component(db, int(id_str))
                if comp and delete_component(db, int(id_str)):
                    create_log_entry(
                        db,
                        LogCreateRequest(
                            action="删除",
                            details=f"删除元器件 ID={id_str}",
                            component_name=comp.name,
                            component_model=comp.model
                        ),
                        "", ""
                    )
                    count += 1
            
            self.selected_ids.clear()
            self.lbl_selected.setText("已选中: 0")
            QMessageBox.information(self, "成功", f"已删除 {count} 条数据")
            self.load_data()
        finally:
            db.close()
    
    def clear_all(self):
        """Clear all data"""
        reply = QMessageBox.warning(
            self, "危险操作",
            "确定要清空所有数据吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        reply2 = QMessageBox.warning(
            self, "再次确认",
            "清空后所有数据将永久删除！\n确定继续吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply2 != QMessageBox.StandardButton.Yes:
            return
        
        db = SessionLocal()
        try:
            count = delete_all_components(db)
            create_log_entry(
                db,
                LogCreateRequest(action="清空", details=f"清空所有元器件，共 {count} 条"),
                "", ""
            )
            self.selected_ids.clear()
            self.lbl_selected.setText("已选中: 0")
            QMessageBox.information(self, "成功", f"已清空 {count} 条数据")
            self.load_data()
        finally:
            db.close()
    
    def show_logs(self):
        """Show operation logs"""
        dialog = LogDialog(self)
        dialog.exec()


def main():
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
