import io

from PIL import Image


def prepare_image(uploaded_file):

    image = Image.open(
        uploaded_file
    )

    image = image.convert(
        "RGB"
    )

    image.thumbnail(
        (2000, 2000)
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=90
    )

    return buffer.getvalue()


def get_image_dimensions(
    uploaded_file
):

    image = Image.open(
        uploaded_file
    )

    return image.size
