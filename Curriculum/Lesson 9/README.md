# Lesson 9: AI Object Detection

Students teach the arm to see. Lessons 6 to 8 turned a target position into joint angles, but the arm still cannot find a cup on the table. Here students run a pretrained object detector on a camera image and turn each detection into a bounding box the arm can act on. On Day 1 they learn what a bounding box is, measure the overlap of two boxes with IoU, and run a pretrained model that already knows 80 everyday object classes. On Day 2 they clean up the detector's output with a confidence threshold and non-maximum suppression, score it with precision and recall, and use the center of the best box to work out which way the base must turn.

**Time:** two class periods (about 60 minutes each)

## Objectives

By the end of this lesson, students will be able to:

- Explain the difference between classifying an image and detecting objects in it
- Read a bounding box in corner format and in (x, y, width, height) format, and find its width, height, center and area
- Calculate the IoU (intersection over union) of two boxes and explain why 0.5 is a common match rule
- Describe what a pretrained model is, and what a detector returns for each object: a box, a label and a confidence score
- Run a pretrained detector on an image and read its output
- Apply a confidence threshold and non-maximum suppression, and explain the trade-off each one makes
- Calculate precision and recall from counts of true positives, false positives and false negatives
- Turn the center of a target box into a pixel offset and a base turn angle θB

## Files

| File | What it is |
|------|------------|
| [Lesson Plan 9 - AI Object Detection.pdf](Lesson%20Plan%209%20-%20AI%20Object%20Detection.pdf) | Lesson plan with timed procedures, worked answers and assessment |
| [Lesson Plan 9 - AI Object Detection.docx](Lesson%20Plan%209%20-%20AI%20Object%20Detection.docx) | Lesson plan (Word, editable) |
| [Lesson_9_AI_Object_Detection.pdf](Lesson_9_AI_Object_Detection.pdf) | Slides (PDF) |
| [Lesson_9_AI_Object_Detection.pptx](Lesson_9_AI_Object_Detection.pptx) | Slides (PowerPoint, editable) |

## From camera to base angle

1. **Image:** a photo from the arm camera (the examples use 640 × 480)
2. **Detector:** a pretrained YOLOv8 model returns a box, a label and a score for each object
3. **Clean-up:** drop low scores with a confidence threshold, then remove duplicate boxes with NMS (IoU above 0.5)
4. **Target:** pick the best box of the class you want, such as "cup"
5. **Turn angle:** cx = (x_min + x_max) ÷ 2, dx = cx − W ÷ 2, f = (W ÷ 2) ÷ tan(HFOV ÷ 2) and θ = atan(dx ÷ f). A target on the right (dx > 0) means a negative θB.

The worked example turns the box (400, 150, 500, 350) into θB = −13.2° for a 60° field of view. One camera gives the direction but not the distance. Lesson 10 adds the depth.

## Code

The code for this lesson is in the [Code folder](../../Code/). Install the packages with `pip install ultralytics opencv-python`. The first run downloads the small pretrained model (yolov8n.pt), so it needs internet access once. Keep the files in one folder, because the script imports `detect_helper.py`.

| Day | File | What it does |
|-----|------|--------------|
| 1–2 | [`detect_helper.py`](../../Code/detect_helper.py) | Box math (size, center, area, IoU), `filter_by_score`, `nms`, `precision_recall`, `pixel_offset`, `turn_angle`, `pick_target`, plus `run_detector` and `draw_detections` |
| 2 | [`detect_pipeline.py`](../../Code/detect_pipeline.py) | The whole pipeline: detect, filter, NMS, pick the best cup and print its center, offset and base turn |

Put an arm-camera photo named `table.png` in the same folder before running the script. When the best cup box is (400, 150, 500, 350), it prints a center of (450.0, 250.0), an offset of 130.0 10.0 and a base turn of −13.2 degrees. The box math was tested; run `run_detector` once on a lab computer before class.

**Previous:** [Lesson 7](../Lesson%207/) (Lesson 8 is planned) · **Next:** [Lesson 10: Stereoscopic Camera](../Lesson%2010/)
