from PIL import Image, ImageDraw, ImageFont
from floatrange import floatrange


def draw_ruler(draw, width, height, bottom_margin_ratio, tick_count, offset_maximum):
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
