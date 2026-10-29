from stereo_helper import focal_px, depth_from_disparity

f = focal_px(640, 60)          # Lesson 9: about 554 px
x_L, x_R = 412, 298            # read from the two images
Z = depth_from_disparity(x_L - x_R, f, 60)
print(round(Z), "mm")          # 292
