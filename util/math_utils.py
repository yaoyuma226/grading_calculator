import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPolygonF


def distance(p1: QPointF, p2: QPointF) -> float:
    return math.sqrt((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2)


def get_angle(start_pos: QPointF, end_pos: QPointF) -> float:
    # Calculate the angle of the arrow
    delta_x = end_pos.x() - start_pos.x()
    delta_y = end_pos.y() - start_pos.y()
    return math.atan2(delta_y, delta_x)


def get_cos(angle: float) -> float:
    return math.cos(angle)


def get_arrow_head(angle: float, end_pos: QPointF) -> QPolygonF:
    arrow_head_size = 10
    # Calculate the arrowhead points
    arrow_p1 = QPointF(
        end_pos.x() - arrow_head_size * math.cos(angle - math.pi / 6),
        end_pos.y() - arrow_head_size * math.sin(angle - math.pi / 6),
    )
    arrow_p2 = QPointF(
        end_pos.x() - arrow_head_size * math.cos(angle + math.pi / 6),
        end_pos.y() - arrow_head_size * math.sin(angle + math.pi / 6),
    )

    return QPolygonF([end_pos, arrow_p1, arrow_p2])


def get_closest_point(points, target_point):
    # Calculate the distance between the target point and each point
    distances = [distance(point, target_point) for point in points]

    # Find the index of the point with the minimum distance
    min_distance_index = distances.index(min(distances))

    # Return the closest point
    return points[min_distance_index]


def calculate_gradient_descent(
    start_point: QPointF,
    target_point: QPointF,
    height: float,
    beta: float,
    scale: float,
    descent: float,
):
    # Calculate the gradient between the two nearest points
    d = distance(start_point, target_point)
    alpha = get_angle(start_point, target_point)
    d_orth = d * get_cos(alpha - beta)
    print(f"distance {d} d_orth {d_orth}")
    d_scaled = d_orth * scale
    print(f"d_scaled {d_scaled}")
    drop = d_scaled / 100 * descent
    print(f"drop {drop}")
    new_h = height - drop
    print(f"new height {new_h}")
    return new_h
