import ctypes
import string
import sys

import sdl2.sdlimage
from sdl2 import *

from sdl_rect_ascii import SdlRectAscii

FONT_WIDTH = 128
FONT_HEIGHT = 64
FONT_COLS = 18
FONT_ROWS = 7
FONT_CHAR_WIDTH = FONT_WIDTH / FONT_COLS
FONT_CHAR_HEIGHT = FONT_HEIGHT / FONT_ROWS

ACSII_DISPLAY_LOW = 32
# TODO(jan): Maybe 126
ACSII_DISPLAY_HIGH = 127

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_POS_X, SCREEN_POS_Y = (1920 - SCREEN_WIDTH) // 2, (
        1080 - SCREEN_HEIGHT
) // 2


def scc(code):
    if code < 0:
        print(f"SDL ERROR: {SDL_GetError()}")
        sys.exit(1)


def scp(ptr):
    if ptr == 0:
        print(f"SDL ERROR: {SDL_GetError()}")
        sys.exit(1)
    return ptr


def surface_from_file(file_path):
    """
    :param file_path: Accept file name as a string
    :return data.contents: As SDL_Surface object
    """
    data = sdl2.sdlimage.IMG_Load(file_path)

    if not data:
        print(f"IMG_Load ERROR: {sdl2.sdlimage.IMG_GetError()}")
        sys.exit(1)
    return data.contents


def font_object():
    """
    Create black SDL_Texture and 95 of free list space
    :return dict
    """
    font = {
        "spritesheet": SDL_Texture(),
        "glyph_table": [0] * (ACSII_DISPLAY_HIGH - ACSII_DISPLAY_LOW),
    }
    return font


def font_load_from_file(renderer, file_path):
    """
    :return dict
    """
    font = font_object()

    font_surface = surface_from_file(file_path)
    font["spritesheet"] = scp(
        SDL_CreateTextureFromSurface(renderer, font_surface)
    )

    SDL_FreeSurface(font_surface)

    for asci in range(ACSII_DISPLAY_LOW, ACSII_DISPLAY_HIGH):
        # print(f"ASCII: {asci}, {ACSII_DISPLAY_HIGH - ACSII_DISPLAY_LOW}")
        index = asci - ACSII_DISPLAY_LOW
        # print(f"Index: {chr(index)} -> {index} - 32 = {index - 32}")
        # Get each letters in which col -> know col
        col = int(index % FONT_COLS)
        # print(f"Index: {index} % {FONT_COLS} = Col {col}")
        # Get each letters in which row -> know row
        row = int(index / FONT_COLS)
        # print(f"Index: {index} / {FONT_COLS} = Row {row}")

        font["glyph_table"][index] = SdlRectAscii(
            x=int(col * FONT_CHAR_WIDTH),
            y=int(row * FONT_CHAR_HEIGHT),
            w=int(FONT_CHAR_WIDTH),
            h=int(FONT_CHAR_HEIGHT),
            asci=asci,
        )
        # print(
        #     asci,
        #     type(font["glyph_table"][index]),
        #     font["glyph_table"][index],
        # )

    return font


def render_char(renderer, font, c, x, y, scale):
    dst = SDL_Rect(
        x=int(x),
        y=int(y),
        w=int(FONT_CHAR_WIDTH * scale),
        h=int(FONT_CHAR_HEIGHT * scale),
    )

    # print(c)
    assert c >= ACSII_DISPLAY_LOW
    assert c <= ACSII_DISPLAY_HIGH
    index = c - ACSII_DISPLAY_LOW
    # print(index, c, chr(c), font["glyph_table"][index])

    scc(
        SDL_RenderCopy(
            renderer,
            font["spritesheet"],
            font["glyph_table"][index].get_lp_sdl_rect,
            dst,
        )
    )


def renderer_text_sized(renderer, font, text, text_size, x, y, color, scale):
    SDL_SetTextureColorMod(
        font["spritesheet"],
        # 2 left digits -> R
        color >> (8 * 2) & 0xFF,
        # 2 middle digits -> G
        color >> (8 * 1) & 0xFF,
        # 2 right digits -> B
        color >> (8 * 0) & 0xFF,
    )

    scc(SDL_SetTextureAlphaMod(font["spritesheet"], color >> (8 * 3) & 0xFF))

    for i in range(text_size):
        render_char(renderer, font, ord(text[i]), x, y, scale)
        x += FONT_CHAR_WIDTH * scale
    return True


def renderer_text(renderer, font, text, x, y, color, scale):
    renderer_text_sized(renderer, font, text, len(text), x, y, color, scale)


def main():
    scc(SDL_Init(SDL_INIT_VIDEO))
    scc(sdl2.sdlimage.IMG_Init(sdl2.sdlimage.IMG_INIT_PNG))
    window = SDL_CreateWindow(
        b"Sus Editor",
        SCREEN_POS_X,
        SCREEN_POS_Y,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SDL_WINDOW_RESIZABLE,
    )
    renderer = scp(SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED))

    font = font_load_from_file(renderer, b"charmap-oldschool_white.png")

    buffer_capacity = 1024
    buffer = []
    buffer_size = 0
    while True:
        event = scp(SDL_Event())
        if SDL_PollEvent(ctypes.byref(event)) != 0:
            if event.type == SDL_QUIT:
                break
            else:
                if SDL_TEXTINPUT:
                    # 1 -> char, 0 -> nothing
                    text_size = len(event.text.text)
                    # It minus all the time
                    free_space = buffer_capacity - buffer_size
                    try:
                        text = event.text.text.decode("utf-8")
                        if text != "" and text in string.ascii_letters + string.punctuation + string.digits:
                            if text_size > free_space:
                                text_size = free_space
                            if free_space == 0:
                                pass
                            else:
                                buffer.append(text)
                                buffer_size += text_size
                        else:
                            pass
                    except UnicodeDecodeError:
                        pass

                scc(SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0))
                scc(SDL_RenderClear(renderer))
                renderer_text_sized(
                    renderer, font, buffer, buffer_size, 0, 0, 0x00FFFF, 5
                )
                SDL_RenderPresent(renderer)
    SDL_Quit()
    return 0


main()
