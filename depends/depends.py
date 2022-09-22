# -*- coding: utf-8 -*-
class Depends:
    def __init__(self, f, *args, **kwargs):
        self.f = f
        self.args = args
        self.kwargs = kwargs
