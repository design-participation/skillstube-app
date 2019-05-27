from PIL import Image

def make_thumbnail(filename, output, target_size=512):
    image = Image.open(filename)
    if image is None:
        return False
    exif = image._getexif()
    width, height = image.size

    x = y = 0
    if width > height:
        x = (width - height) // 2
        size = height
    else:
        y = (height - width) // 2
        size = width
    image = image.resize((target_size, target_size), box=(x, y, x + size, y + size))
    ORIENTATION = 274
    if exif is not None and ORIENTATION in exif:
        orientation = exif[ORIENTATION]
        method = {2: Image.FLIP_LEFT_RIGHT, 4: Image.FLIP_TOP_BOTTOM, 8: Image.ROTATE_90, 3: Image.ROTATE_180, 6: Image.ROTATE_270, 5: Image.TRANSPOSE, 7: Image.TRANSVERSE}
        if orientation in method:
            image = image.transpose(method[orientation])
    try:
        image.save(output, quality=65)
    except IOError as e:
        print(e)
        return False
    return True

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print('usage: %s <source.jpg> <dest.jpg>' % sys.argv[0])
        sys.exit(1)
    make_thumbnail(sys.argv[1], sys.argv[2])
