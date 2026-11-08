from PIL import Image
im = Image.open(r"D:/Softfors/jup/assets/figures/remedfilm_inference_infographic.png")
print("size", im.size, "mode", im.mode, "aspect", round(im.size[0]/im.size[1], 3))
