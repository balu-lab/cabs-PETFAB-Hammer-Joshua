"""Helper functions for the AI Object Detection lesson.
Boxes are (x_min, y_min, x_max, y_max) in pixels. The origin (0, 0) is the
TOP-LEFT corner of the image, x grows to the right and y grows DOWNWARD.
"""
import math


def box_size(box):
    """Width and height of a box."""
    x1, y1, x2, y2 = box
    return x2 - x1, y2 - y1


def box_area(box):
    w, h = box_size(box)
    return max(w, 0) * max(h, 0)


def box_center(box):
    """Center point (cx, cy) of a box."""
    x1, y1, x2, y2 = box
    return (x1 + x2) / 2, (y1 + y2) / 2


def xyxy_to_xywh(box):
    """Corner format -> (x_min, y_min, width, height)."""
    x1, y1, x2, y2 = box
    return x1, y1, x2 - x1, y2 - y1


def xywh_to_xyxy(box):
    """(x_min, y_min, width, height) -> corner format."""
    x, y, w, h = box
    return x, y, x + w, y + h


def iou(a, b):
    """Intersection over Union of two boxes (0 = no overlap, 1 = identical)."""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(ix2 - ix1, 0) * max(iy2 - iy1, 0)
    union = box_area(a) + box_area(b) - inter
    return inter / union if union > 0 else 0.0


def filter_by_score(detections, threshold):
    """Keep detections whose score is at least threshold.
    Each detection is a dict:
    {"box": (x1, y1, x2, y2), "label": str, "score": float}
    """
    return [d for d in detections if d["score"] >= threshold]


def nms(detections, iou_threshold=0.5):
    """Non-maximum suppression. For each label, keep the best box and drop
    any lower-scoring box that overlaps it by more than iou_threshold."""
    kept = []
    for d in sorted(detections, key=lambda d: d["score"], reverse=True):
        clash = any(k["label"] == d["label"]
                    and iou(k["box"], d["box"]) > iou_threshold
                    for k in kept)
        if not clash:
            kept.append(d)
    return kept


def precision_recall(tp, fp, fn):
    """Precision = TP / (TP + FP). Recall = TP / (TP + FN)."""
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r


def pixel_offset(box, image_w, image_h):
    """How far the box center is from the image center, in pixels.
    Positive dx = target is to the RIGHT. Positive dy = target is BELOW."""
    cx, cy = box_center(box)
    return cx - image_w / 2, cy - image_h / 2


def turn_angle(dx, image_w, hfov_deg):
    """Angle (degrees) between the camera's forward direction and a pixel dx
    pixels from the image center. Pinhole model: tan(angle) = dx / f."""
    f = (image_w / 2) / math.tan(math.radians(hfov_deg) / 2)  # in pixels
    return math.degrees(math.atan(dx / f))


def pick_target(detections, label):
    """The highest-scoring detection with the given label, or None."""
    matches = [d for d in detections if d["label"] == label]
    return max(matches, key=lambda d: d["score"]) if matches else None


def run_detector(image_path, model_name="yolov8n.pt", conf=0.25):
    """Run a pretrained YOLO model (trained on COCO's 80 classes) on one image.
    Returns a list of {"box", "label", "score"} dicts.
    Needs: pip install ultralytics
    """
    from ultralytics import YOLO
    model = YOLO(model_name)  # downloads the weights the first time
    result = model(image_path, conf=conf, verbose=False)[0]
    out = []
    for b in result.boxes:
        x1, y1, x2, y2 = [float(v) for v in b.xyxy[0]]
        out.append({"box": (x1, y1, x2, y2),
                    "label": result.names[int(b.cls[0])],
                    "score": float(b.conf[0])})
    return out


def draw_detections(image_path, detections, out_path="detections.png"):
    """Draw each box and its label + score on the image and save it."""
    import cv2
    img = cv2.imread(image_path)
    for d in detections:
        x1, y1, x2, y2 = [int(v) for v in d["box"]]
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 200, 0), 2)
        text = f'{d["label"]} {d["score"]:.2f}'
        cv2.putText(img, text, (x1, max(y1 - 6, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
    cv2.imwrite(out_path, img)
    return out_path


if __name__ == "__main__":
    A, B = (100, 100, 300, 300), (200, 200, 400, 400)
    print(round(iou(A, B), 4))  # expected: 0.1429
