######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Classes for drawing graphics items on QGraphicsScene.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""

from math import atan2, sin, cos, pi
from PySide2.QtCore import Qt, Slot, QPointF, QLineF, QRectF, QVariantAnimation
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsTextItem,
    QGraphicsSimpleTextItem,
    QGraphicsRectItem,
    QStyle,
    QGraphicsColorizeEffect,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PySide2.QtGui import (
    QColor,
    QPen,
    QBrush,
    QPainterPath,
    QTextCursor,
    QTransform,
    QPalette,
    QTextBlockFormat,
    QLinearGradient,
)
from PySide2.QtSvg import QGraphicsSvgItem, QSvgRenderer


class ConnectorButton(QGraphicsRectItem):

    # Regular and hover brushes
    brush = QBrush(QColor(255, 255, 255))  # Used in filling the item
    hover_brush = QBrush(QColor(50, 0, 50, 128))  # Used in filling the item while hovering

    def __init__(self, parent, toolbox, position="left"):
        """Connector button graphics item. Used for Link drawing between project items.

        Args:
            parent (QGraphicsItem): Project item bg rectangle
            toolbox (ToolBoxUI): QMainWindow instance
            position (str): Either "top", "left", "bottom", or "right"
        """
        super().__init__()
        self._parent = parent
        self._toolbox = toolbox
        self.position = position
        self.links = list()
        pen = QPen(Qt.black, 0.5, Qt.SolidLine)
        self.setPen(pen)
        self.setBrush(self.brush)
        parent_rect = parent.rect()
        extent = 0.2 * parent_rect.width()
        rect = QRectF(0, 0, extent, extent)
        if position == "top":
            rect.moveCenter(QPointF(parent_rect.center().x(), parent_rect.top() + extent / 2))
        elif position == "left":
            rect.moveCenter(QPointF(parent_rect.left() + extent / 2, parent_rect.center().y()))
        elif position == "bottom":
            rect.moveCenter(QPointF(parent_rect.center().x(), parent_rect.bottom() - extent / 2))
        elif position == "right":
            rect.moveCenter(QPointF(parent_rect.right() - extent / 2, parent_rect.center().y()))
        self.setRect(rect)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)

    def outgoing_links(self):
        return [l for l in self.links if l.src_connector == self]

    def incoming_links(self):
        return [l for l in self.links if l.dst_connector == self]

    def parent_name(self):
        """Returns project item name owning this connector button."""
        return self._parent.name()

    def mousePressEvent(self, event):
        """Connector button mouse press event. Starts drawing a link.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        if not event.button() == Qt.LeftButton:
            event.accept()
        else:
            self._parent.show_item_info()
            # Start drawing a link
            self._toolbox.ui.graphicsView.draw_links(self)

    def mouseDoubleClickEvent(self, event):
        """Connector button mouse double click event. Makes sure the LinkDrawer is hidden.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        event.accept()

    def hoverEnterEvent(self, event):
        """Sets a darker shade to connector button when mouse enters its boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.setBrush(self.hover_brush)

    def hoverLeaveEvent(self, event):
        """Restore original brush when mouse leaves connector button boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.setBrush(self.brush)


class ExclamationIcon(QGraphicsSvgItem):
    def __init__(self, parent):
        """Exclamation icon graphics item.
        Used to notify that a ProjectItem is missing some configuration.

        Args:
            parent (ProjectItemIcon): the parent item
        """
        super().__init__()
        self._parent = parent
        self._notifications = list()
        self.renderer = QSvgRenderer()
        self.colorizer = QGraphicsColorizeEffect()
        self.colorizer.setColor(QColor("red"))
        # Load SVG
        loading_ok = self.renderer.load(":/icons/project_item_icons/exclamation-circle.svg")
        if not loading_ok:
            return
        size = self.renderer.defaultSize()
        self.setSharedRenderer(self.renderer)
        dim_max = max(size.width(), size.height())
        rect_w = parent.rect().width()  # Parent rect width
        self.setScale(0.2 * rect_w / dim_max)
        self.setGraphicsEffect(self.colorizer)
        self._notification_list_item = NotificationListItem()
        self._notification_list_item.setZValue(2)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.hide()

    def clear_notifications(self):
        """Clear all notifications."""
        self._notifications.clear()
        self.hide()

    def add_notification(self, text):
        """Add a notification."""
        self._notifications.append(text)
        self.show()

    def hoverEnterEvent(self, event):
        """Shows notifications as tool tip.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        if not self._notifications:
            return
        tip = "<p>" + "<p>".join(self._notifications)
        self._notification_list_item.setHtml(tip)
        self.scene().addItem(self._notification_list_item)
        self._notification_list_item.setPos(self.sceneBoundingRect().topRight() + QPointF(1, 0))

    def hoverLeaveEvent(self, event):
        """Hides tool tip.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.scene().removeItem(self._notification_list_item)


class NotificationListItem(QGraphicsTextItem):
    def __init__(self):
        """Notification list graphics item.
        Used to show notifications for a ProjectItem
        """
        super().__init__()
        self.bg = QGraphicsRectItem(self.boundingRect(), self)
        bg_brush = QApplication.palette().brush(QPalette.ToolTipBase)
        self.bg.setBrush(bg_brush)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)

    def setHtml(self, html):
        super().setHtml(html)
        self.adjustSize()
        self.bg.setRect(self.boundingRect())


class RankIcon(QGraphicsTextItem):
    def __init__(self, parent):
        """Rank icon graphics item.
        Used to show the rank of a ProjectItem within its DAG

        Args:
            parent (ProjectItemIcon): the parent item
        """
        super().__init__(parent)
        self._parent = parent
        rect_w = parent.rect().width()  # Parent rect width
        self.text_margin = 0.05 * rect_w
        self.bg = QGraphicsRectItem(self.boundingRect(), self)
        bg_brush = QApplication.palette().brush(QPalette.ToolTipBase)
        self.bg.setBrush(bg_brush)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        font = self.font()
        font.setPointSize(parent.text_font_size)
        font.setBold(True)
        self.setFont(font)
        doc = self.document()
        doc.setDocumentMargin(0)

    def set_rank(self, rank):
        self.setPlainText(str(rank))
        self.adjustSize()
        self.setTextWidth(self.text_margin + self.textWidth())
        self.bg.setRect(self.boundingRect())
        # Align center
        fmt = QTextBlockFormat()
        fmt.setAlignment(Qt.AlignHCenter)
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(fmt)
        cursor.clearSelection()
        self.setTextCursor(cursor)


class ProjectItemIcon(QGraphicsRectItem):
    def __init__(self, toolbox, x, y, w, h, project_item, icon_file, icon_color, background_color):
        """Base class for project item icons drawn in Design View.

        Args:
            toolbox (ToolBoxUI): QMainWindow instance
            x (float): Icon x coordinate
            y (float): Icon y coordinate
            w (float): Icon width
            h (float): Icon height
            project_item (ProjectItem): Item
            icon_file (str): Path to icon resource
            icon_color (QColor): Icon's color
            background_color (QColor): Background color
        """
        super().__init__()
        self._toolbox = toolbox
        self._project_item = project_item
        self._moved_on_scene = False
        self.renderer = QSvgRenderer()
        self.svg_item = QGraphicsSvgItem()
        self.colorizer = QGraphicsColorizeEffect()
        self.setRect(QRectF(x, y, w, h))  # Set ellipse coordinates and size
        self.text_font_size = 10  # point size
        # Make item name graphics item.
        name = project_item.name if project_item else ""
        self.name_item = QGraphicsSimpleTextItem(name)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(1)
        shadow_effect.setEnabled(False)
        self.setGraphicsEffect(shadow_effect)
        self.set_name_attributes()  # Set font, size, position, etc.
        # Make connector buttons
        self.connectors = dict(
            bottom=ConnectorButton(self, toolbox, position="bottom"),
            left=ConnectorButton(self, toolbox, position="left"),
            right=ConnectorButton(self, toolbox, position="right"),
        )
        # Make exclamation and rank icons
        self.exclamation_icon = ExclamationIcon(self)
        self.rank_icon = RankIcon(self)
        # Group the drawn items together by setting the background rectangle as the parent of other QGraphicsItems
        # NOTE: setting the parent item moves the items as one!
        self.name_item.setParentItem(self)
        for conn in self.connectors.values():
            conn.setParentItem(self)
        self.svg_item.setParentItem(self)
        self.exclamation_icon.setParentItem(self)
        self.rank_icon.setParentItem(self)
        brush = QBrush(background_color)
        self._setup(brush, icon_file, icon_color)
        # Add items to scene
        scene = self._toolbox.ui.graphicsView.scene()
        scene.addItem(self)

    def _setup(self, brush, svg, svg_color):
        """Setup item's attributes.

        Args:
            brush (QBrush): Used in filling the background rectangle
            svg (str): Path to SVG icon file
            svg_color (QColor): Color of SVG icon
        """
        self.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        self.setBrush(brush)
        self.colorizer.setColor(svg_color)
        # Load SVG
        loading_ok = self.renderer.load(svg)
        if not loading_ok:
            self._toolbox.msg_error.emit("Loading SVG icon from resource:{0} failed".format(svg))
            return
        size = self.renderer.defaultSize()
        self.svg_item.setSharedRenderer(self.renderer)
        self.svg_item.setElementId("")  # guess empty string loads the whole file
        dim_max = max(size.width(), size.height())
        rect_w = self.rect().width()  # Parent rect width
        margin = 32
        self.svg_item.setScale((rect_w - margin) / dim_max)
        x_offset = (rect_w - self.svg_item.sceneBoundingRect().width()) / 2
        y_offset = (rect_w - self.svg_item.sceneBoundingRect().height()) / 2
        self.svg_item.setPos(self.rect().x() + x_offset, self.rect().y() + y_offset)
        self.svg_item.setGraphicsEffect(self.colorizer)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, enabled=True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        # Set exclamation and rank icons position
        self.exclamation_icon.setPos(self.rect().topRight() - self.exclamation_icon.sceneBoundingRect().topRight())
        self.rank_icon.setPos(self.rect().topLeft())

    def name(self):
        """Returns name of the item that is represented by this icon."""
        return self._project_item.name

    def update_name_item(self, new_name):
        """Set a new text to name item. Used when a project item is renamed."""
        self.name_item.setText(new_name)
        self.set_name_attributes()

    def set_name_attributes(self):
        """Set name QGraphicsSimpleTextItem attributes (font, size, position, etc.)"""
        self.name_item.setZValue(3)
        # Set font size and style
        font = self.name_item.font()
        font.setPointSize(self.text_font_size)
        font.setBold(True)
        self.name_item.setFont(font)
        # Set name item position (centered on top of the master icon)
        name_width = self.name_item.boundingRect().width()
        name_height = self.name_item.boundingRect().height()
        self.name_item.setPos(
            self.rect().x() + self.rect().width() / 2 - name_width / 2, self.rect().y() - name_height - 4
        )

    def conn_button(self, position="left"):
        """Returns items connector button (QWidget)."""
        return self.connectors.get(position, self.connectors["left"])

    def outgoing_links(self):
        return [l for conn in self.connectors.values() for l in conn.outgoing_links()]

    def incoming_links(self):
        return [l for conn in self.connectors.values() for l in conn.incoming_links()]

    def hoverEnterEvent(self, event):
        """Sets a drop shadow effect to icon when mouse enters its boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.prepareGeometryChange()
        self.graphicsEffect().setEnabled(True)
        event.accept()

    def hoverLeaveEvent(self, event):
        """Disables the drop shadow when mouse leaves icon boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.prepareGeometryChange()
        self.graphicsEffect().setEnabled(False)
        event.accept()

    def mouseMoveEvent(self, event):
        """Moves icon(s) while the mouse button is pressed.
        Update links that are connected to selected icons.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        super().mouseMoveEvent(event)
        selected_icons = set(x for x in self.scene().selectedItems() if isinstance(x, ProjectItemIcon))
        links = set(link for icon in selected_icons for conn in icon.connectors.values() for link in conn.links)
        for link in links:
            link.update_geometry()

    def mouseReleaseEvent(self, event):
        if self._moved_on_scene:
            self._moved_on_scene = False
            self.scene().shrink_if_needed()
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        """Show item context menu.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        self.scene().clearSelection()
        self.setSelected(True)
        self._toolbox.show_item_image_context_menu(event.screenPos(), self.name())

    def keyPressEvent(self, event):
        """Handles deleting and rotating the selected
        item when dedicated keys are pressed.

        Args:
            event (QKeyEvent): Key event
        """
        if event.key() == Qt.Key_Delete and self.isSelected():
            ind = self._toolbox.project_item_model.find_item(self.name())
            delete_int = int(self._toolbox.qsettings().value("appSettings/deleteData", defaultValue="0"))
            delete_bool = delete_int != 0
            self._toolbox.remove_item(ind, delete_item=delete_bool)
            event.accept()
        elif event.key() == Qt.Key_R and self.isSelected():
            # TODO:
            # 1. Change name item text direction when rotating
            # 2. Save rotation into project file
            rect = self.mapToScene(self.boundingRect()).boundingRect()
            center = rect.center()
            t = QTransform()
            t.translate(center.x(), center.y())
            t.rotate(90)
            t.translate(-center.x(), -center.y())
            self.setPos(t.map(self.pos()))
            self.setRotation(self.rotation() + 90)
            links = set(lnk for conn in self.connectors.values() for lnk in conn.links)
            for link in links:
                link.update_geometry()
            event.accept()
        else:
            super().keyPressEvent(event)

    def itemChange(self, change, value):
        """
        Reacts to item removal and position changes.

        In particular, destroys the drop shadow effect when the items is removed from a scene
        and keeps track of item's movements on the scene.

        Args:
            change (GraphicsItemChange): a flag signalling the type of the change
            value: a value related to the change

        Returns:
             Whatever super() does with the value parameter
        """
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._moved_on_scene = True
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange and value is None:
            self.prepareGeometryChange()
            self.setGraphicsEffect(None)
        return super().itemChange(change, value)

    def show_item_info(self):
        """Update GUI to show the details of the selected item."""
        ind = self._toolbox.project_item_model.find_item(self.name())
        self._toolbox.ui.treeView_project.setCurrentIndex(ind)


class LinkBase(QGraphicsPathItem):
    """Base class for Link and LinkDrawer.

    Mainly provides the `update_geometry` method for 'drawing' the link on the scene.
    """

    def __init__(self, toolbox):
        """Initializes the instance.

        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__()
        self._toolbox = toolbox
        self.arrow_angle = pi / 4
        self.magic_number = None

    @property
    def src_rect(self):
        """Returns the scene rectangle of the source connector."""
        return self.src_connector.sceneBoundingRect()

    @property
    def src_center(self):
        """Returns the center point of the source rectangle."""
        return self.src_rect.center()

    @property
    def dst_rect(self):
        """Returns the scene rectangle of the destination connector."""
        return self.dst_connector.sceneBoundingRect()

    @property
    def dst_center(self):
        """Returns the center point of the destination rectangle."""
        return self.dst_rect.center()

    def update_geometry(self):
        """Updates geometry."""
        self.prepareGeometryChange()
        qsettings = self._toolbox.qsettings()
        smooth_links = qsettings.value("appSettings/smoothLinks", defaultValue="false") == "true"
        self.do_update_geometry(smooth_links)

    def do_update_geometry(self, smooth_links):
        """Sets the path for this item.

        Args:
            smooth_links (bool): Whether the path should follow a smooth curve or just a straight line
        """
        ellipse_path = self._make_ellipse_path()
        guide_path = self._make_guide_path(smooth_links)
        connecting_path = self._make_connecting_path(guide_path)
        arrow_path = self._make_arrow_path(guide_path)
        path = ellipse_path + connecting_path + arrow_path
        self.setPath(path.simplified())

    def _make_ellipse_path(self):
        """Returns an ellipse path for the link's base.

        Returns:
            QPainterPath
        """
        ellipse_path = QPainterPath()
        rect = QRectF(0, 0, 1.6 * self.magic_number, 1.6 * self.magic_number)
        rect.moveCenter(self.src_center)
        ellipse_path.addEllipse(rect)
        return ellipse_path

    def _get_src_offset(self):
        if self.src_connector == self.dst_connector:
            return {"left": QPointF(0, 1), "bottom": QPointF(1, 0), "right": QPointF(0, -1)}[
                self.src_connector.position
            ]
        return {"left": QPointF(-1, 0), "bottom": QPointF(0, 1), "right": QPointF(1, 0)}[self.src_connector.position]

    def _get_dst_offset(self):
        if not self.dst_connector:
            return QPointF(0, 0)
        return {"left": QPointF(-1, 0), "bottom": QPointF(0, 1), "right": QPointF(1, 0)}[self.dst_connector.position]

    def _make_guide_path(self, smooth_links):
        """
        Returns a 'narrow' path conneting this item's source and destination.

        Args:
            smooth_links (bool): Whether the path should follow a smooth curve or just a straight line

        Returns:
            QPainterPath
        """
        smooth_links |= self.dst_connector == self.src_connector
        path = QPainterPath(self.src_center)
        if not smooth_links:
            path.lineTo(self.dst_center)
            return path
        c_factor = 8 * self.magic_number
        src_offset = self._get_src_offset()
        dst_offset = self._get_dst_offset()
        c1 = self.src_center + c_factor * src_offset
        c2 = self.dst_center + c_factor * dst_offset
        path.cubicTo(c1, c2, self.dst_center)
        return path

    def _path_to_points(self, path):
        """Returns a list of representative points from given path.

        Args:
            path (QPainterPath)

        Returns:
            list(QPointF)
        """
        length = path.length() - self.src_rect.width() / 2
        points = list()
        i = 0.0
        max_incr = 10.0
        min_incr = 0.1
        s_change_tol = 0.5
        while i < length:
            t0 = path.percentAtLength(i)
            p0 = path.pointAtPercent(t0)
            s0 = path.slopeAtPercent(t0)
            points.append(p0)
            incr = max_incr
            while incr > min_incr:
                t1 = path.percentAtLength(i + incr)
                s1 = path.slopeAtPercent(t1)
                try:
                    s_change = abs((s1 - s0) / s0)
                except ZeroDivisionError:
                    incr = min_incr
                    break
                if s_change < s_change_tol:
                    break
                incr /= 2
            i += incr
        t = path.percentAtLength(length)
        points.append(path.pointAtPercent(t))
        points.append(path.pointAtPercent(1.0))
        return points

    def _make_connecting_path(self, guide_path):
        """Returns a 'thick' path connecting source and destination, by following the given 'guide' path.

        Args:
            guide_path (QPainterPath)

        Returns:
            QPainterPath
        """
        points = self._path_to_points(guide_path)
        off = self._get_normal_offset(points[0], points[1])
        lower_points = [points[0] + off]
        upper_points = [points[0] - off]
        for src, dst in zip(points[:-1], points[1:]):
            off = self._get_normal_offset(src, dst)
            lower_points.append(src + off)
            upper_points.append(src - off)
        all_points = lower_points + list(reversed(upper_points))
        p0 = all_points.pop(0)
        curve_path = QPainterPath(p0)
        curve_path.setFillRule(Qt.WindingFill)
        for p in all_points:
            curve_path.lineTo(p)
        curve_path.lineTo(p0)
        return curve_path

    def _get_normal_offset(self, src, dst):
        normal = QLineF(src, dst).normalVector()
        normal.setLength(self.magic_number / 2)
        return QPointF(normal.dx(), normal.dy())

    def _make_arrow_path(self, guide_path):
        """Returns an arrow path for the link's tip.

        Args:
            guide_path (QPainterPath): A narrow path connecting source and destination,
                used to determine the arrow orientation.

        Returns:
            QPainterPath
        """
        angle = self._get_join_angle(guide_path)
        arrow_p0 = self.dst_center
        d1 = QPointF(sin(angle + self.arrow_angle), cos(angle + self.arrow_angle))
        d2 = QPointF(sin(angle + (pi - self.arrow_angle)), cos(angle + (pi - self.arrow_angle)))
        arrow_diag = self.magic_number / sin(self.arrow_angle)
        arrow_p1 = arrow_p0 - d1 * arrow_diag
        arrow_p2 = arrow_p0 - d2 * arrow_diag
        arrow_path = QPainterPath(arrow_p1)
        arrow_path.lineTo(arrow_p0)
        arrow_path.lineTo(arrow_p2)
        arrow_path.closeSubpath()
        return arrow_path

    @staticmethod
    def _get_join_angle(guide_path):
        src = guide_path.pointAtPercent(0.99)
        dst = guide_path.pointAtPercent(1.0)
        line = QLineF(src, dst)
        return atan2(-line.dy(), line.dx())


class Link(LinkBase):
    def __init__(self, toolbox, src_connector, dst_connector):
        """A graphics item to represent the connection between two project items.

        Args:
            toolbox (ToolboxUI): main UI class instance
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
        """
        super().__init__(toolbox)
        self.src_connector = src_connector  # QGraphicsRectItem
        self.dst_connector = dst_connector
        self.src_icon = src_connector._parent
        self.dst_icon = dst_connector._parent
        self.setZValue(1)
        # Path parameters
        self.magic_number = 0.625 * self.src_rect.width()
        self.setToolTip(
            "<html><p>Connection from <b>{0}</b>'s output "
            "to <b>{1}</b>'s input</html>".format(self.src_icon.name(), self.dst_icon.name())
        )
        self.setBrush(QBrush(QColor(255, 255, 0, 204)))
        self.selected_pen = QPen(Qt.black, 1, Qt.DashLine)
        self.normal_pen = QPen(Qt.black, 0.5)
        self.parallel_link = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setCursor(Qt.PointingHandCursor)
        self.update_geometry()

    def make_execution_animation(self):
        """Returns an animation to play when execution 'passes' through this link.

        Returns:
            QVariantAnimation
        """
        qsettings = self._toolbox.qsettings()
        duration = int(qsettings.value("appSettings/dataFlowAnimationDuration", defaultValue="100"))
        animation = QVariantAnimation()
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setDuration(duration)
        animation.valueChanged.connect(self._handle_execution_animation_value_changed)
        animation.finished.connect(lambda: self.setBrush(QColor(255, 255, 0, 204)))
        animation.finished.connect(animation.deleteLater)
        return animation

    @Slot("QVariant")
    def _handle_execution_animation_value_changed(self, step):
        gradient = QLinearGradient(self.src_center, self.dst_center)
        yellow = QColor(255, 255, 0, 204)
        red = QColor(255, 0, 0, 204)
        delta = 8 * self.magic_number / QLineF(self.src_center, self.dst_center).length()
        gradient.setColorAt(0, yellow)
        gradient.setColorAt(max(0.0, step - delta), yellow)
        gradient.setColorAt(step, red)
        gradient.setColorAt(min(1.0, step + delta), yellow)
        gradient.setColorAt(1.0, yellow)
        self.setBrush(gradient)

    def has_parallel_link(self):
        """Returns whether or not this link entirely overlaps another."""
        self.parallel_link = next(
            iter(l for l in self.dst_connector.outgoing_links() if l.dst_connector == self.src_connector), None
        )
        return self.parallel_link is not None

    def send_to_bottom(self):
        """Stacks this link before the parallel one if any."""
        if self.parallel_link:
            self.stackBefore(self.parallel_link)

    def mousePressEvent(self, e):
        """Ignores event if there's a connector button underneath,
        to allow creation of new links.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if e.button() != Qt.LeftButton:
            e.ignore()
        elif any(isinstance(x, ConnectorButton) for x in self.scene().items(e.scenePos())):
            e.ignore()

    def mouseDoubleClickEvent(self, e):
        """Accepts event if there's a connector button underneath,
        to prevent unwanted creation of feedback links.
        """
        if any(isinstance(x, ConnectorButton) for x in self.scene().items(e.scenePos())):
            e.accept()

    def contextMenuEvent(self, e):
        """Selects the link and shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        self.setSelected(True)
        self._toolbox.show_link_context_menu(e.screenPos(), self)

    def keyPressEvent(self, event):
        """Removes this link if delete is pressed."""
        if event.key() == Qt.Key_Delete and self.isSelected():
            self._toolbox.ui.graphicsView.remove_link(self)

    def paint(self, painter, option, widget):
        """Sets a dashed pen if selected."""
        if option.state & QStyle.State_Selected:
            option.state &= ~QStyle.State_Selected
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def itemChange(self, change, value):
        """Brings selected link to top."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and value == 1:
            for item in self.collidingItems():  # TODO: try using scene().collidingItems() which is ordered
                if not isinstance(item, Link):
                    continue
                item.stackBefore(self)
            return value
        return super().itemChange(change, value)

    def wipe_out(self):
        """Removes any trace of this item from the system."""
        self.src_connector.links.remove(self)
        if self.src_connector != self.dst_connector:
            self.dst_connector.links.remove(self)
        scene = self.scene()
        if scene:
            scene.removeItem(self)


class LinkDrawer(LinkBase):
    def __init__(self, toolbox):
        """An item for drawing links between project items.

        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__(toolbox)
        self.src_connector = None  # source connector
        self.tip = None
        self.drawing = False
        self.setBrush(QBrush(QColor(255, 0, 255, 204)))
        self.setPen(QPen(Qt.black, 0.5))
        self.setZValue(2)
        self.hide()

    def start_drawing_at(self, src_connector):
        """Starts drawing a link from the given connector.

        Args:
            src_connector (ConnectorButton)
        """
        self.src_connector = src_connector
        self.tip = self.src_center
        self.magic_number = 0.625 * self.src_rect.width()
        self.update_geometry()
        self.show()

    @property
    def dst_connector(self):
        items = self.scene().items(self.tip)
        return next(iter(x for x in items if isinstance(x, ConnectorButton)), None)

    @property
    def dst_rect(self):
        if not self.dst_connector:
            return QRectF()
        return self.dst_connector.sceneBoundingRect()

    @property
    def dst_center(self):
        if not self.dst_connector:
            return self.tip
        return self.dst_rect.center()
