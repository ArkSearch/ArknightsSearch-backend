__all__ = ['Extra', 'ExtraData']

import re
from pydantic import BaseModel
from typing import Literal, Callable

from .search import StorySearchParamGroup, StorySearchParam
from .data import *


class TextData(BaseModel):
    type: Literal['text'] = 'text'
    data: list[list[str | None]]
    has_more: bool
    raw: str

    @classmethod
    def get(cls, match: list[list[str]], raw: str) -> 'TextData':
        self = cls.__new__(cls)
        if len(match) > 5:
            self.__init__(data=match[:5], raw=raw, has_more=True)
        else:
            self.__init__(data=match, raw=raw, has_more=False)
        return self


class CharData(BaseModel):
    type: Literal['char'] = 'char'
    data: list[str]
    has_more: bool
    raw: str

    @classmethod
    def get(cls, match: list[str], raw: str) -> 'CharData':
        self = cls.__new__(cls)
        if len(match) > 5:
            self.__init__(data=match[:5], has_more=True, raw=raw)
        else:
            self.__init__(data=match, has_more=False, raw=raw)
        return self

    @staticmethod
    def get_handler(param: StorySearchParam) -> Callable[[str], 'CharData']:
        char_possible_names = set()
        # 该角色名对应的所有可能的名称
        [[char_possible_names.add(name) for name in char_id2name[char_id]]
         for char_id in char_name2id[param.param]]
        regex = re.compile(r'^(?:%s):.*' % '|'.join(char_possible_names), flags=re.MULTILINE)

        # TODO 真路人npc名称查找问题

        def handler(text: str) -> CharData:
            """
            CharData handler
            :param text:故事文本
            :return: CharData
            """
            return CharData.get(regex.findall(text), param.param)

        return handler


ExtraData = TextData | CharData


class Extra:
    text_regex = r'(?:(.*)\n)?(.*)(%s)(.*)(?:\n((?:.(?!%s))*)$)?'
    char_regex = r'^%s:.*'

    # TODO 异名id提取 `“焰尾”索娜`

    """提取数据，提供快速搜索"""

    def __init__(self, params: StorySearchParamGroup):
        self.params: StorySearchParamGroup = params
        self.text_params: list[str] = [i.param for i in params if i.type == 'text']
        self.text_regexes = [(i, re.compile(self.text_regex % (i, i), flags=re.MULTILINE)) for i in self.text_params]
        self.char_handlers = [CharData.get_handler(i) for i in self.params if i.type == 'char']

    def get(self, story_id: str) -> list[ExtraData]:
        text = text_data['zh_CN'][story_id]
        match = [TextData.get(r[1].findall(text), r[0]) for r in self.text_regexes] \
                + [handler(text) for handler in self.char_handlers]
        return match
