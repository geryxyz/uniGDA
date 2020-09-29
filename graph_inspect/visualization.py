import io

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngImageFile
from floatrange import floatrange


def draw_ruler(draw, width, height, bottom_margin_ratio, tick_count, offset_maximum):
    if offset_maximum != 0:
        rule_font = ImageFont.truetype('arial', size=int(height * bottom_margin_ratio * .6))
        for value in floatrange(0, offset_maximum, offset_maximum / tick_count):
            mark = f'{value:.4f}'
            text_width, text_height = rule_font.getsize(mark)
            offset = int((value / offset_maximum) * width)
            if offset_maximum - value < text_width:
                draw.line([(offset, height * (1 - bottom_margin_ratio) + 3), (offset, height)],
                          fill=(0, 0, 0, 255))
                draw.text((offset - text_width - 3, height - text_height), mark, fill=(0, 0, 0, 255),
                          font=rule_font)
            elif value < text_width:
                draw.line([(offset, height * (1 - bottom_margin_ratio) + 3), (offset, height)],
                          fill=(0, 0, 0, 255))
                draw.text((offset + 3, height - text_height), mark, fill=(0, 0, 0, 255), font=rule_font)
            else:
                draw.line([(offset, height * (1 - bottom_margin_ratio) + 3), (offset, height - text_height - 2)],
                          fill=(0, 0, 0, 255))
                draw.text((offset - (text_width / 2), height - text_height), mark, fill=(0, 0, 0, 255),
                          font=rule_font)


def text_with_boarder(draw: ImageDraw, position, text: str, font: ImageFont, text_fill=(0, 0, 0, 255), box_fill=(255, 255, 255, 255), box_boarder=(0, 0, 0, 255), margin: int = 2):
    text_width, text_height = font.getsize(text)
    draw.rectangle(
        [(position[0] - text_width / 2 - margin, position[1] - text_height / 2 - margin),
         (position[0] + text_width / 2 + margin, position[1] + text_height / 2 + margin)],
        outline=box_boarder, fill=box_fill)
    draw.text((position[0] - text_width / 2, position[1] - text_height / 2), text, fill=text_fill, font=font)


class NDDVisualization(object):
    def __init__(self, figure, axes):
        self.figure = figure
        self.axes = axes

    @property
    def image(self) -> PngImageFile:
        buffer = io.BytesIO()
        self.figure.savefig(buffer, format='png')
        self.figure.clf()
        buffer.seek(0)
        image = Image.open(buffer)
        image.load()
        buffer.close()
        return image

