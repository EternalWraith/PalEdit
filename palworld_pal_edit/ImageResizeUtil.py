from PIL import Image
import os

for root, dirs, files in os.walk("resources/pals"):
    for name in files:
        i = Image.open(os.path.join(root, name))
        ni = i.resize((240,240))
        ni.save(os.path.join(root,name))

